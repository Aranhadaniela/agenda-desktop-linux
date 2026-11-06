import {parseEvents, dayGroups} from '../desktop/gnome/events.js';

function assert(condition, message) {
    if (!condition)
        throw new Error(message);
}
function event(inicio, fim, dia_inteiro = false) {
    return {titulo: '<b>Sintético</b>', inicio, fim, dia_inteiro};
}
function parse(values) {
    return parseEvents(JSON.stringify({eventos: values}));
}
const now = new Date('2026-11-05T10:00:00-03:00');
const values = parse([
    event('2026-11-04', '2026-11-07', true),
    event('2026-11-05', '2026-11-06', true),
    event('2026-11-06', null, true),
    event('2026-11-05T15:00:00Z', '2026-11-05T16:00:00Z'),
    event('2026-11-05T09:00:00-03:00', '2026-11-05T10:00:00-03:00'),
    event('2026-11-05T23:00:00-03:00', '2026-11-06T01:00:00-03:00'),
    event('2026-11-06T08:00:00-03:00', null),
]);
const groups = dayGroups(values, now);
assert(groups[0].events.length === 4, 'today intersection and expired timed event');
assert(groups[1].events.length === 4, 'tomorrow: exclusive end, multiday and missing end');
assert(values[0].start.getDate() === 4 && values[0].start.getHours() === 0, 'all-day stays local');
assert(values.find(value => !value.allDay && value.start.getHours() === 12), 'UTC converts to local');
assert(values[0].title === '<b>Sintético</b>', 'titles remain literal text');
for (const value of [event('2026-02-30', null, true), event('2026-11-05T12:00:00', null), event('2026-11-05', '2026-11-04', true)]) {
    let failed = false;
    try { parse([value]); } catch (_error) { failed = true; }
    assert(failed, 'invalid dates must fail');
}
print('GNOME event tests passed');
