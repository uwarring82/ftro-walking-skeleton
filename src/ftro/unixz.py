#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Unix compress (.Z) LZW codec, pure standard library.

Python ships no LZW decoder, and this repository's policy is standard library only.
A .Z magic-byte check is not a content check: any two bytes can be prefixed to
arbitrary junk.  To assert that retrieved bytes really are the product they claim
to be, the stream has to be decoded.

Format (compress(1) / ncompress, LZW as in Welch 1984):
  byte 0,1  magic 0x1f 0x9d
  byte 2    flags: bits 0-4 maxbits (9..16), bit 0x80 block mode
  then      LZW codes packed LSB-first, width 9 bits growing to maxbits.

Two quirks that a naive LZW reader gets wrong, both reproduced here:

  * Block mode reserves code 256 as CLEAR (reset the string table, drop back to
    9-bit codes).  Codes 0..255 are the literals, so the first assignable code is
    257, not 256.

  * compress(1) buffers output in groups of eight codes (n_bits bytes).  When the
    code width grows, and after a CLEAR, it flushes that whole group zero-padded,
    because the decoder cannot see the width change until it has read the group.
    The decoder must therefore skip to the next group boundary at those two points.
    The boundary is measured from the last skip, not from the start of the stream:
    each width phase starts its own group grid.
"""

MAGIC = b"\x1f\x9d"
BIT_MASK = 0x1F
BLOCK_MODE = 0x80
INIT_BITS = 9
CLEAR = 256
FIRST = 257          # first assignable code in block mode


class UnixCompressError(ValueError):
    """Malformed .Z stream."""


def _code_at(data, bitpos, n_bits):
    i = bitpos >> 3
    chunk = data[i:i + 3]
    if len(chunk) < 3:
        chunk = chunk + b"\x00" * (3 - len(chunk))
    return (int.from_bytes(chunk, "little") >> (bitpos & 7)) & ((1 << n_bits) - 1)


def _next_boundary(pos, origin, n_bits):
    """Skip to the next 8-code group boundary measured from `origin`.

    Mirrors ncompress:
        posbits = (posbits-1) + ((n_bits<<3) - (posbits-1+(n_bits<<3)) % (n_bits<<3))
    i.e. round (pos-1) strictly up to the next multiple of n_bits*8.
    """
    block = n_bits << 3
    local = pos - origin - 1
    return origin + ((local // block) + 1) * block


def decompress(data, max_output=None):
    """Decode a Unix compress (.Z) stream.  Returns bytes.

    max_output: optional ceiling on decoded size.  Retrieval validation runs on
    bytes fetched from the network, so an unbounded decode is a denial-of-service
    surface; callers that validate untrusted input should set this.
    """
    if len(data) < 3:
        raise UnixCompressError("stream shorter than the 3-byte header")
    if data[0:2] != MAGIC:
        raise UnixCompressError(
            f"bad magic {data[0:2].hex()}, expected {MAGIC.hex()}")
    flags = data[2]
    maxbits = flags & BIT_MASK
    block_mode = bool(flags & BLOCK_MODE)
    if not INIT_BITS <= maxbits <= 16:
        raise UnixCompressError(f"maxbits {maxbits} outside the legal range 9..16")
    maxmaxcode = 1 << maxbits

    n_bits = INIT_BITS
    maxcode = maxmaxcode if n_bits == maxbits else (1 << n_bits) - 1
    table = [bytes((i,)) for i in range(256)] + [b""] * (maxmaxcode - 256)
    next_code = FIRST if block_mode else 256
    prev = -1
    out = bytearray()

    total_bits = len(data) << 3
    origin = 24                      # code stream starts after the 3-byte header
    pos = 24

    while pos + n_bits <= total_bits:
        if next_code > maxcode and n_bits < maxbits:
            pos = _next_boundary(pos, origin, n_bits)
            origin = pos
            n_bits += 1
            maxcode = maxmaxcode if n_bits == maxbits else (1 << n_bits) - 1
            continue

        code = _code_at(data, pos, n_bits)
        pos += n_bits

        if block_mode and code == CLEAR:
            table[FIRST:] = [b""] * (maxmaxcode - FIRST)
            next_code = FIRST
            prev = -1
            pos = _next_boundary(pos, origin, n_bits)
            origin = pos
            n_bits = INIT_BITS
            maxcode = maxmaxcode if n_bits == maxbits else (1 << n_bits) - 1
            continue

        if prev < 0:
            if code >= 256:
                raise UnixCompressError(
                    f"first code {code} is not a literal")
            out.append(code)
            prev = code
            continue

        if code < next_code and table[code]:
            entry = table[code]
        elif code == next_code:
            entry = table[prev] + table[prev][:1]      # KwKwK
        else:
            raise UnixCompressError(
                f"code {code} exceeds table size {next_code} at bit {pos - n_bits}")

        out += entry
        if max_output is not None and len(out) > max_output:
            raise UnixCompressError(f"decoded output exceeds {max_output} bytes")
        if next_code < maxmaxcode:
            table[next_code] = table[prev] + entry[:1]
            next_code += 1
        prev = code

    return bytes(out)


def compress(data, maxbits=16, block_mode=True, clear_every=None):
    """Encode bytes as a Unix compress (.Z) stream.

    Written so that test fixtures are synthesised from committed code rather than
    copied from a provider, and so the decoder above can be checked round-trip and
    against compress(1).  Mirrors the encoder in ncompress, including the
    zero-padded group flush on width growth and on CLEAR.

    clear_every: emit a CLEAR code every N input symbols consumed, to exercise
    the block-mode reset path and its group padding deliberately.  None means no
    CLEAR is ever emitted (this encoder simply stops extending a full table).
    """
    if not INIT_BITS <= maxbits <= 16:
        raise ValueError("maxbits must be 9..16")
    if clear_every is not None and not block_mode:
        raise ValueError("CLEAR requires block mode")
    maxmaxcode = 1 << maxbits
    out = bytearray(MAGIC)
    out.append(maxbits | (BLOCK_MODE if block_mode else 0))

    state = {"n_bits": INIT_BITS,
             "maxcode": (maxmaxcode if INIT_BITS == maxbits else (1 << INIT_BITS) - 1),
             "buf": bytearray(),      # bits of the current group, LSB-first
             "nbuf": 0}

    def emit(code, free_ent, clear_flg=False):
        n = state["n_bits"]
        bitpos = state["nbuf"]
        buf = state["buf"]
        while len(buf) < (bitpos + n + 7) // 8:
            buf.append(0)
        v = code << (bitpos & 7)
        i = bitpos >> 3
        while v:
            buf[i] |= v & 0xFF
            v >>= 8
            i += 1
        state["nbuf"] += n
        if state["nbuf"] == (n << 3):          # group of eight codes complete
            out.extend(buf[:n])
            del buf[:]
            state["nbuf"] = 0
        if free_ent > state["maxcode"] or clear_flg:
            if state["nbuf"] > 0:              # zero-pad the partial group
                out.extend((bytes(buf) + b"\x00" * n)[:n])
                del buf[:]
                state["nbuf"] = 0
            if clear_flg:
                state["n_bits"] = INIT_BITS
                state["maxcode"] = (maxmaxcode if INIT_BITS == maxbits
                                    else (1 << INIT_BITS) - 1)
            elif state["n_bits"] < maxbits:
                state["n_bits"] += 1
                state["maxcode"] = (maxmaxcode if state["n_bits"] == maxbits
                                    else (1 << state["n_bits"]) - 1)

    def flush_tail():
        if state["nbuf"] > 0:
            out.extend(bytes(state["buf"])[:(state["nbuf"] + 7) // 8])
            del state["buf"][:]
            state["nbuf"] = 0

    if not data:
        return bytes(out)

    table = {}
    free_ent = FIRST if block_mode else 256
    ent = data[0]
    consumed = 1
    last_clear = 0
    for c in data[1:]:
        consumed += 1
        key = (ent, c)
        if key in table:
            ent = table[key]
            continue
        emit(ent, free_ent)
        if free_ent < maxmaxcode:
            table[key] = free_ent
            free_ent += 1
        ent = c
        if clear_every and consumed - last_clear >= clear_every:
            emit(CLEAR, free_ent, clear_flg=True)
            table.clear()
            free_ent = FIRST
            last_clear = consumed
    emit(ent, free_ent)
    flush_tail()
    return bytes(out)


if __name__ == "__main__":
    import sys
    sys.stdout.buffer.write(decompress(sys.stdin.buffer.read()))
