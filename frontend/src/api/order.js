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

export const getOrders = (params) => {
    return request.get('/order/list', {
        params: {
            status: params.status,
            page: params.page,
            per_page: params.perPage,
            start_date: params.startDate,
            end_date: params.endDate,
            query: params.query
        }
    })
}

export const refundOrder = (data) => {
    return request.post('/order/refund', data)
}
