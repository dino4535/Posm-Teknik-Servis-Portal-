import { useRef } from 'react'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import trLocale from '@fullcalendar/core/locales/tr'
import '../styles/RequestCalendar.css'

function RequestCalendar({ requests, onEventClick }) {
  const calendarRef = useRef(null)

  // Talepleri FullCalendar event formatına çevir
  const events = requests.map(request => {
    let className = 'status-beklemede'
    if (request.durum === 'Tamamlandı') {
      className = 'status-tamamlandi'
    } else if (request.planlananTarih) {
      className = 'status-planlandi'
    }

    // Tarihi parse et
    let eventDate
    if (request.planlananTarih) {
      // DD.MM.YYYY formatından Date'e çevir
      const parts = request.planlananTarih.split('.')
      if (parts.length === 3) {
        eventDate = new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0]))
      }
    }
    
    if (!eventDate || isNaN(eventDate.getTime())) {
      // Planlanan tarih yoksa talep tarihini kullan
      const talepParts = request.talepTarihi.split(' ')
      if (talepParts.length > 0) {
        const dateParts = talepParts[0].split('.')
        if (dateParts.length === 3) {
          eventDate = new Date(parseInt(dateParts[2]), parseInt(dateParts[1]) - 1, parseInt(dateParts[0]))
        }
      }
    }

    if (!eventDate || isNaN(eventDate.getTime())) {
      return null
    }

    // Başlığı kısalt
    let title = request.bayiAdi || 'Bayi'
    if (title.length > 20) {
      title = title.substring(0, 17) + '...'
    }

    return {
      id: request.id.toString(),
      title: title,
      start: eventDate.toISOString().split('T')[0],
      allDay: true,
      className: className,
      extendedProps: {
        bayiAdi: request.bayiAdi,
        yapilacakIs: request.yapilacakIs,
        durum: request.durum,
        talepTarihi: request.talepTarihi,
        planlananTarih: request.planlananTarih
      }
    }
  }).filter(event => event !== null)

  return (
    <div className="calendar-container">
      <FullCalendar
        ref={calendarRef}
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        locale={trLocale}
        height="auto"
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,dayGridWeek'
        }}
        buttonText={{
          today: 'Bugün',
          month: 'Ay',
          week: 'Hafta'
        }}
        dayMaxEvents={3}
        events={events}
        eventClick={(info) => {
          if (onEventClick) {
            onEventClick(parseInt(info.event.id))
          }
        }}
        eventDidMount={(info) => {
          // Tooltip ekle
          const event = info.event
          const tooltip = `
            <div style="text-align: left; line-height: 1.4;">
              <strong>${event.extendedProps.bayiAdi}</strong><br>
              <small>
                ${event.extendedProps.yapilacakIs}<br>
                Talep: ${event.extendedProps.talepTarihi}<br>
                Plan: ${event.extendedProps.planlananTarih || 'Planlama Bekleniyor'}<br>
                Durum: ${event.extendedProps.durum}
              </small>
            </div>
          `
          info.el.setAttribute('title', tooltip)
        }}
        moreLinkContent={(args) => {
          return '+' + args.num + ' talep'
        }}
      />
    </div>
  )
}

export default RequestCalendar
