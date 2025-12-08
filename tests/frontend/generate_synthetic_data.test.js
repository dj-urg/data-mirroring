/**
 * @jest-environment jsdom
 */

const { getPersonaLabel, getActivityLabel } = require('../../src/app/static/js/generate_synthetic_data.js');

describe('Synthetic Data Generators', () => {
    test('getPersonaLabel returns correct labels', () => {
        expect(getPersonaLabel('career')).toBe('Career Professional');
        expect(getPersonaLabel('unknown')).toBe('unknown');
    });

    test('getActivityLabel returns correct labels', () => {
        expect(getActivityLabel('high')).toBe('high (power user)');
        expect(getActivityLabel('low')).toBe('low (occasional user)');
    });
});
