import {parseEvents, dayGroups} from '../desktop/gnome/events.js';
for (const [date, expected] of [['2026-03-08', 23], ['2026-11-01', 25]]) {
    const events = parseEvents(JSON.stringify({eventos: [
        {titulo: 'Sintético', inicio: date, fim: null, dia_inteiro: true},
    ]}));
    const event = events[0];
    if ((event.end - event.start) / 3600000 !== expected)
        throw new Error('All-day duration must follow DST');
    const groups = dayGroups(events, new Date(`${date}T12:00:00`));
    if (groups[0].events.length !== 1 || groups[1].events.length !== 0)
        throw new Error('Exclusive civil end must survive DST');
}
print('GNOME DST tests passed');
