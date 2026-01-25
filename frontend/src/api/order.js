import request from './request'

export const createOrder = (data) => {
    return request.post('/order/create', data)
}

export const payOrder = (data) => {
    return request.post('/order/pay', data)
}

export const cancelOrder = (data) => {
    return request.post('/order/cancel', data)
}

export const getOrders = (status, page, perPage) => {
    return request.get('/order/list', { params: { status, page, per_page: perPage } })
}

export const refundOrder = (data) => {
    return request.post('/order/refund', data)
}
