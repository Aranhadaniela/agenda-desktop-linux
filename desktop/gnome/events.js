// Pure data functions: no Shell objects, markup, network or filesystem access.
function dateOnly(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value))
        throw new Error('Invalid date');
    // Never parse YYYY-MM-DD as UTC: all-day events are civil local dates.
    const [year, month, day] = value.split('-').map(Number);
    const result = new Date(0);
    result.setFullYear(year, month - 1, day);
    result.setHours(0, 0, 0, 0);
    if (result.getFullYear() !== year || result.getMonth() !== month - 1 || result.getDate() !== day)
        throw new Error('Invalid date');
    return result;
}

function eventTime(value, allDay) {
    if (allDay)
        return dateOnly(value);
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value))
        throw new Error('Missing timezone');
    dateOnly(value.slice(0, 10));
    const result = new Date(value);
    if (!Number.isFinite(result.getTime()))
        throw new Error('Invalid timestamp');
    return result;
}

export function parseEvents(text) {
    if (text.length > 2 * 1024 * 1024)
        throw new Error('Cache too large');
    const data = JSON.parse(text);
    if (!data || !Array.isArray(data.eventos) || data.eventos.length > 5000)
        throw new Error('Invalid events');
    return data.eventos.map(event => {
        if (!event || typeof event.titulo !== 'string' || typeof event.dia_inteiro !== 'boolean')
            throw new Error('Invalid event');
        const start = eventTime(event.inicio, event.dia_inteiro);
        let end = event.fim === null ? null : eventTime(event.fim, event.dia_inteiro);
        if (end === null) {
            end = new Date(start);
            if (event.dia_inteiro)
                end.setDate(end.getDate() + 1);
        }
        if (end < start || (event.dia_inteiro && end <= start))
            throw new Error('Invalid interval');
        return {title: event.titulo.slice(0, 1000), start, end, allDay: event.dia_inteiro};
    }).sort((a, b) => a.start - b.start);
}

export function dayGroups(events, now = new Date()) {
    const today = new Date(now);
    today.setHours(0, 0, 0, 0);
    return [0, 1].map(offset => {
        const day = new Date(today);
        day.setDate(day.getDate() + offset);
        const end = new Date(day);
        end.setDate(end.getDate() + 1);
        return {
            title: offset === 0 ? 'HOJE' : 'AMANHÃ',
            events: events.filter(event => {
                if (event.end.getTime() === event.start.getTime())
                    return event.start >= day && event.start < end && event.start >= now;
                return event.start < end && event.end > day && (event.allDay || event.end > now);
            }),
        };
    });
}
