import request from './request'

export const getStats = () => {
    return request.get('/admin/stats')
}

export const getUsers = (page, perPage) => {
    return request.get('/admin/users', { params: { page, per_page: perPage } })
}

export const updateUser = (data) => {
    return request.post('/admin/user/update', data)
}

export const updateParking = (data) => {
    return request.post('/admin/parking/update', data)
}

export const getAllOrders = (page, perPage, status) => {
    return request.get('/admin/orders', { params: { page, per_page: perPage, status } })
}
