import { io } from 'socket.io-client'
import { useParkingStore } from '@/stores/parking'

let socket = null

export const initWebSocket = () => {
    if (socket) return socket

    socket = io(window.location.origin, {
        transports: ['websocket', 'polling']
    })

    socket.on('connect', () => {
        console.log('WebSocket connected')
    })

    socket.on('disconnect', () => {
        console.log('WebSocket disconnected')
    })

    socket.on('spot_status_update', (data) => {
        console.log('Spot status update:', data)
        const parkingStore = useParkingStore()
        parkingStore.updateSpotStatus(data.spot_id, data.status, data.current_plate)
    })

    return socket
}

export const closeWebSocket = () => {
    if (socket) {
        socket.close()
        socket = null
    }
}

export const getSocket = () => socket
