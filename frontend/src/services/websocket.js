import { io } from 'socket.io-client'
import { ElNotification } from 'element-plus'

class WebSocketService {
  constructor() {
    this.socket = null
    this.listeners = new Map()
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
  }

  connect(url = 'http://127.0.0.1:5001') {
    if (this.socket?.connected) {
      return this.socket
    }

    this.socket = io(url, {
      transports: ['websocket', 'polling'],
      timeout: 5000,
      forceNew: true
    })

    this.setupEventListeners()
    return this.socket
  }

  setupEventListeners() {
    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
      
      // 连接成功后请求初始数据
      this.requestData('all')
    })

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason)
      
      if (reason === 'io server disconnect') {
        // 服务器主动断开，尝试重连
        this.handleReconnect()
      }
    })

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error)
      this.handleReconnect()
    })

    this.socket.on('data_update', (data) => {
      console.log('Received data update:', data.type)
      this.notifyListeners(data.type, data.data)
    })
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      
      setTimeout(() => {
        this.socket.connect()
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      ElNotification.error({
        title: '连接失败',
        message: '无法连接到服务器，请刷新页面重试',
        duration: 0
      })
    }
  }

  requestData(type) {
    if (this.socket?.connected) {
      this.socket.emit('request_data', { type })
    }
  }

  // 订阅数据更新
  subscribe(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set())
    }
    this.listeners.get(eventType).add(callback)

    // 返回取消订阅函数
    return () => {
      const callbacks = this.listeners.get(eventType)
      if (callbacks) {
        callbacks.delete(callback)
        if (callbacks.size === 0) {
          this.listeners.delete(eventType)
        }
      }
    }
  }

  // 通知所有监听器
  notifyListeners(eventType, data) {
    const callbacks = this.listeners.get(eventType)
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error('Error in WebSocket callback:', error)
        }
      })
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.listeners.clear()
  }

  isConnected() {
    return this.socket?.connected || false
  }
}

// 创建单例实例
export const websocketService = new WebSocketService()
export default websocketService