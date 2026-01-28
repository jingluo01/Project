/**
 * 支付相关API
 */
import request from '@/api/request'

/**
 * 创建支付宝支付二维码
 */
export const createAlipayQRCode = (data) => {
    return request({
        url: '/payment/alipay/qrcode',
        method: 'post',
        data
    })
}

/**
 * 查询支付宝支付状态
 */
export const queryAlipayStatus = (params) => {
    return request({
        url: '/payment/alipay/query',
        method: 'get',
        params
    })
}
