import request from './request'

export const getStats = () => {
    return request.get('/admin/stats')
}

export const getAdminConfig = () => {
    return request.get('/admin/config')
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

export const getAllOrders = (params) => {
    return request.get('/admin/orders', {
        params: {
            page: params.page,
            per_page: params.perPage,
            status: params.status,
            start_date: params.startDate,
            end_date: params.endDate,
            query: params.query
        }
    })
}

export const forceExitOrder = (plate_number) => {
    return request.post('/admin/order/force-exit', { plate_number })
}

export const updateAdminConfig = (data) => {
    return request.post('/admin/config/update', data)
}
