import request from './request'

export const getProfile = () => {
    return request.get('/user/profile')
}

export const bindCar = (data) => {
    return request.post('/user/car/bind', data)
}

export const removeCar = (carId) => {
    return request.delete(`/user/car/remove/${carId}`)
}

export const recharge = (data) => {
    return request.post('/user/recharge', data)
}
