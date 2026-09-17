"""
Forward Error Correction (FEC) Framework — extensible plugin architecture.
"""
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple


class FECDetector(ABC):
    """Base class for FEC type detection."""
    @abstractmethod
    def detect(self, bits: List[int]) -> Dict[str, Any]:
        """Attempt to detect FEC encoding in bit sequence."""
        pass


class FECDecoder(ABC):
    """Base class for FEC decoding."""
    @abstractmethod
    def decode(self, bits: List[int], **kwargs) -> Dict[str, Any]:
        """Decode FEC-encoded bit sequence."""
        pass


class InterleaverDetector(ABC):
    """Base class for interleaver detection."""
    @abstractmethod
    def detect(self, bits: List[int]) -> Dict[str, Any]:
        pass


class Deinterleaver(ABC):
    """Base class for de-interleaving."""
    @abstractmethod
    def deinterleave(self, bits: List[int], **kwargs) -> List[int]:
        pass


# ──────────────────────── Hamming Code ────────────────────────

class HammingDecoder(FECDecoder):
    """Hamming(7,4) decoder — corrects single-bit errors."""

    def decode(self, bits: List[int], **kwargs) -> Dict[str, Any]:
        if len(bits) < 7:
            return {"success": False, "error": "Insufficient bits for Hamming(7,4)"}

        decoded_bits = []
        corrections = 0
        blocks = len(bits) // 7

        for i in range(blocks):
            block = bits[i*7:(i+1)*7]
            data, corrected = self._decode_block(block)
            decoded_bits.extend(data)
            if corrected:
                corrections += 1

        return {
            "success": True,
            "decoded_bits": decoded_bits,
            "original_bits": len(bits),
            "decoded_length": len(decoded_bits),
            "corrections": corrections,
            "code": "Hamming(7,4)",
        }

    def _decode_block(self, block: List[int]) -> Tuple[List[int], bool]:
        """Decode one Hamming(7,4) block."""
        d = block
        # Syndrome calculation
        s0 = d[0] ^ d[2] ^ d[4] ^ d[6]
        s1 = d[1] ^ d[2] ^ d[5] ^ d[6]
        s2 = d[3] ^ d[4] ^ d[5] ^ d[6]
        syndrome = s0 + s1 * 2 + s2 * 4

        corrected = False
        if syndrome != 0:
            error_pos = syndrome - 1
            if error_pos < 7:
                d[error_pos] ^= 1
                corrected = True

        # Extract data bits (positions 2, 4, 5, 6 in 0-indexed)
        return [d[2], d[4], d[5], d[6]], corrected


class HammingDetector(FECDetector):
    """Detect if bitstream might be Hamming-encoded."""

    def detect(self, bits: List[int]) -> Dict[str, Any]:
        if len(bits) < 70:  # Need at least 10 blocks
            return {"detected": False, "reason": "Insufficient data"}

        # Check if block length is consistent with Hamming(7,4)
        decoder = HammingDecoder()
        result = decoder.decode(bits[:700])
        correction_rate = result.get("corrections", 0) / max(1, len(bits) // 7)

        # If very few corrections needed, might be Hamming-encoded
        return {
            "detected": correction_rate < 0.3,
            "confidence": max(0, 1.0 - correction_rate),
            "code": "Hamming(7,4)",
            "correction_rate": correction_rate,
        }


# ──────────────────────── Block Interleaver ────────────────────────

class BlockDeinterleaver(Deinterleaver):
    """Simple block de-interleaver."""

    def deinterleave(self, bits: List[int], rows: int = 8, cols: int = 8, **kwargs) -> List[int]:
        block_size = rows * cols
        if len(bits) < block_size:
            return bits

        result = []
        num_blocks = len(bits) // block_size

        for b in range(num_blocks):
            block = bits[b*block_size:(b+1)*block_size]
            # Read column-wise (de-interleave)
            matrix = np.array(block).reshape(rows, cols)
            result.extend(matrix.T.flatten().tolist())

        # Remainder
        remainder = bits[num_blocks*block_size:]
        result.extend(remainder)

        return result


class BlockInterleaverDetector(InterleaverDetector):
    """Attempt to detect block interleaving."""

    def detect(self, bits: List[int]) -> Dict[str, Any]:
        return {
            "detected": False,
            "reason": "Automatic interleaver detection not reliable without reference",
            "confidence": 0.0,
        }


# ──────────────────────── FEC Registry ────────────────────────

_fec_decoders: Dict[str, FECDecoder] = {
    "hamming74": HammingDecoder(),
}

_fec_detectors: Dict[str, FECDetector] = {
    "hamming": HammingDetector(),
}

_deinterleavers: Dict[str, Deinterleaver] = {
    "block": BlockDeinterleaver(),
}

_interleaver_detectors: Dict[str, InterleaverDetector] = {
    "block": BlockInterleaverDetector(),
}


def detect_fec(bits: List[int]) -> Dict[str, Any]:
    """Try all registered FEC detectors."""
    results = {}
    for name, detector in _fec_detectors.items():
        try:
            results[name] = detector.detect(bits)
        except Exception as e:
            results[name] = {"detected": False, "error": str(e)}

    detected = [name for name, r in results.items() if r.get("detected")]
    if detected:
        best = max(detected, key=lambda n: results[n].get("confidence", 0))
        return {
            "detected": True,
            "fec_type": results[best].get("code", best),
            "confidence": results[best].get("confidence", 0),
            "details": results,
        }

    return {
        "detected": False,
        "message": "FEC type could not be reliably identified.",
        "details": results,
    }


def decode_fec(bits: List[int], fec_type: str = "hamming74") -> Dict[str, Any]:
    """Decode using specified FEC decoder."""
    decoder = _fec_decoders.get(fec_type)
    if decoder is None:
        return {"success": False, "error": f"Unknown FEC type: {fec_type}"}
    return decoder.decode(bits)


def register_decoder(name: str, decoder: FECDecoder):
    """Register a new FEC decoder plugin."""
    _fec_decoders[name] = decoder


def register_detector(name: str, detector: FECDetector):
    """Register a new FEC detector plugin."""
    _fec_detectors[name] = detector
