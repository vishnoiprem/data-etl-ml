export function decodeZOrderCurve(mortonCode, numBits, coordinateShift) {
    const x = decodeMorton(mortonCode, numBits) - coordinateShift;
    const y = decodeMorton(mortonCode >> 1, numBits) - coordinateShift;
    return { x, y };
}
function decodeMorton(code, numBits) {
    let coordinate = 0;
    for (let i = 0; i < numBits; i++) {
        coordinate |= (code & (1 << (2 * i))) >> i;
    }
    return coordinate;
}
//# sourceMappingURL=zOrderCurve.js.map