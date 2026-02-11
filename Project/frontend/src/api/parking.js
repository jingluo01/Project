import request from './request'

export const getZones = () => {
    return request.get('/parking/zones')
}

export const getSpots = (zoneId) => {
    return request.get('/parking/spots', { params: { zone_id: zoneId } })
}

export const vehicleEnter = (data) => {
    return request.post('/parking/enter', data)
}

export const vehicleExit = (data) => {
    return request.post('/parking/exit', data)
}
