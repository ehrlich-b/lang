// Numeric libc boundary shared by the LLVM compiler host and direct-Wasm host.
// Models validate their restricted literal grammar before reaching strtod.
'use strict';

(function (scope) {
  function parseCDecimal(text) {
    const match = String(text).match(/^[\t\n\v\f\r ]*([+-]?(?:(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|infinity|inf|nan(?:\([A-Za-z0-9_]*\))?))/i);
    if (!match) return { value: 0, consumed: 0 };
    const token = match[1];
    const value = /^[+-]?nan/i.test(token) ? NaN
      : /^[+-]?inf/i.test(token) ? (token[0] === '-' ? -Infinity : Infinity)
      : Number(token);
    return { value, consumed: match[0].length };
  }

  function exponentSuffix(exponent) {
    return `e${exponent < 0 ? '-' : '+'}${String(Math.abs(exponent)).padStart(2, '0')}`;
  }

  function formatGeneral(value, precision = 6) {
    if (!Number.isFinite(value)) return Number.isNaN(value) ? 'nan' : value < 0 ? '-inf' : 'inf';
    if (value === 0) return Object.is(value, -0) ? '-0' : '0';
    precision = Math.max(1, precision);
    const sign = value < 0 ? '-' : '';
    const [mantissa, power] = Math.abs(value).toExponential(precision - 1).split('e');
    const exponent = Number(power);
    if (exponent < -4 || exponent >= precision) {
      return sign + mantissa.replace(/\.?0+$/, '') + exponentSuffix(exponent);
    }
    const digits = mantissa.replace('.', '');
    const point = exponent + 1;
    let fixed = point <= 0 ? `0.${'0'.repeat(-point)}${digits}`
      : point >= digits.length ? digits + '0'.repeat(point - digits.length)
      : `${digits.slice(0, point)}.${digits.slice(point)}`;
    if (fixed.includes('.')) fixed = fixed.replace(/\.?0+$/, '');
    return sign + fixed;
  }

  function specs(format) {
    return [...format.matchAll(/%(?:%|(?:\.(\d+))?(?:ll|l)?([dfgeis]))/g)]
      .filter(match => match[0] !== '%%');
  }

  function formatNumericPrintf(format, values) {
    let index = 0;
    return format.replace(/%(?:%|(?:\.(\d+))?(?:ll|l)?([dfgeis]))/g, (whole, digits, kind) => {
      if (whole === '%%') return '%';
      if (index >= values.length) throw new Error('printf is missing a numeric argument');
      const value = values[index++];
      const precision = digits === undefined ? 6 : Number(digits);
      if (precision > 100) throw new Error('printf precision exceeds 100');
      if (kind === 'd' || kind === 'i' || kind === 's') return String(value);
      const number = Number(value);
      if (kind === 'g') return formatGeneral(number, precision);
      if (!Number.isFinite(number)) return Number.isNaN(number) ? 'nan' : number < 0 ? '-inf' : 'inf';
      const sign = Object.is(number, -0) ? '-' : '';
      if (kind === 'f') {
        // Binary64 values at this scale are integers. toFixed itself switches
        // to exponent notation at 1e21, while C's %f keeps the integer digits.
        if (Math.abs(number) >= 1e21) return BigInt(number).toString()
          + (precision ? '.' + '0'.repeat(precision) : '');
        return sign + number.toFixed(precision);
      }
      const [mantissa, exponent] = number.toExponential(precision).split('e');
      return sign + mantissa + exponentSuffix(Number(exponent));
    });
  }

  function createNumericHost({ memory, cstr, emit, pointerBytes = 8 }) {
    const view = () => new DataView(memory().buffer);
    function output(format, values) {
      const kinds = specs(format);
      const decoded = values.map((value, index) => kinds[index]?.[2] === 's' ? cstr(value) : value);
      const text = formatNumericPrintf(format, decoded);
      emit(text, false);
      return BigInt(new TextEncoder().encode(text).length);
    }
    return {
      fmod: (left, right) => left % right,
      fmodf: (left, right) => Math.fround(Math.fround(left) % Math.fround(right)),
      strtod(textPointer, endPointer) {
        const parsed = parseCDecimal(cstr(textPointer));
        if (Number(endPointer) !== 0) {
          const end = BigInt(textPointer) + BigInt(parsed.consumed);
          if (pointerBytes === 4) view().setUint32(Number(endPointer), Number(end), true);
          else view().setBigUint64(Number(endPointer), end, true);
        }
        return parsed.value;
      },
      printf(formatPointer, ...values) { return output(cstr(formatPointer), values); },
      printfBuffer(formatPointer, argumentPointer) {
        const format = cstr(formatPointer);
        let offset = Number(argumentPointer);
        const values = specs(format).map(spec => {
          const value = spec[2] === 'd' || spec[2] === 'i' || spec[2] === 's'
            ? view().getBigInt64(offset, true) : view().getFloat64(offset, true);
          offset += 8;
          return value;
        });
        return output(format, values);
      },
    };
  }

  const api = { parseCDecimal, formatGeneral, formatNumericPrintf, createNumericHost };
  if (typeof module !== 'undefined') module.exports = api;
  scope.LangNumericHost = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
