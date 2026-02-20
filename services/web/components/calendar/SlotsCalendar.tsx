/**
 * @file: SlotsCalendar.tsx
 * @description: Виджет FullCalendar — слоты как события, клик по свободному открывает заказ.
 * @dependencies: @fullcalendar/react, @fullcalendar/core, daygrid, timegrid, interaction
 * @created: 2025-02-20
 */
"use client";

import { useCallback } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import ruLocale from "@fullcalendar/core/locales/ru";

export type Slot = { id: string; channel_id: string; datetime: string; status: string };

type SlotsCalendarProps = {
  slots: Slot[];
  onSlotClick?: (slot: Slot) => void;
  height?: string | number;
};

function slotToEvent(slot: Slot): {
  id: string;
  start: string;
  title: string;
  backgroundColor: string;
  extendedProps: { slot: Slot };
} {
  const start = slot.datetime.replace(" ", "T");
  const isFree = slot.status === "free";
  return {
    id: slot.id,
    start,
    title: isFree ? "Свободен" : "Занят",
    backgroundColor: isFree ? "#10b981" : "#64748b",
    extendedProps: { slot },
  };
}

export function SlotsCalendar({ slots, onSlotClick, height = 400 }: SlotsCalendarProps) {
  const events = slots.map(slotToEvent);

  const handleEventClick = useCallback(
    (info: { event: { id: string; extendedProps: { slot: Slot } } }) => {
      const slot = info.event.extendedProps.slot;
      if (slot.status === "free" && onSlotClick) onSlotClick(slot);
    },
    [onSlotClick]
  );

  return (
    <div className="slots-calendar [&_.fc]:rounded-lg [&_.fc-toolbar-title]:text-base [&_.fc-col-header-cell-cushion]:text-slate-600 [&_.fc-daygrid-day-number]:text-slate-500">
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"
        headerToolbar={{
          left: "prev,next today",
          center: "title",
          right: "dayGridMonth,timeGridWeek,timeGridDay",
        }}
        locale={ruLocale}
        events={events}
        eventClick={handleEventClick}
        height={height}
        slotMinTime="00:00:00"
        slotMaxTime="24:00:00"
        nowIndicator
        eventDisplay="block"
      />
    </div>
  );
}
