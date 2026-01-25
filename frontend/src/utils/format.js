export const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN')
}

export const formatCurrency = (amount) => {
    return `¥${Number(amount).toFixed(2)}`
}

export const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (hours > 0) {
        return `${hours}小时${minutes}分钟`
    }
    return `${minutes}分钟`
}

export const getOrderStatusText = (status) => {
    const statusMap = {
        0: '已预约',
        1: '进行中',
        2: '待支付',
        3: '已完成',
        4: '已取消',
        5: '已退款',
        6: '超时违约'
    }
    return statusMap[status] || '未知'
}

export const getOrderStatusType = (status) => {
    const typeMap = {
        0: 'primary',   // 已预约 - 蓝色
        1: '',          // 进行中 - 紫色（自定义）
        2: 'warning',   // 待支付 - 橙色
        3: 'success',   // 已完成 - 绿色
        4: 'info',      // 已取消 - 灰色
        5: '',          // 已退款 - 青色（自定义）
        6: 'danger'     // 超时违约 - 红色
    }
    return typeMap[status] !== undefined ? typeMap[status] : 'info'
}

export const getRoleText = (role) => {
    const roleMap = {
        0: '外部用户',
        1: '学生',
        2: '教职工',
        3: '管理员'
    }
    return roleMap[role] || '未知'
}
