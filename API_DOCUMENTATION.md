# Market AI V3 - Backend API Documentation

**Version:** 3.0.0  
**Last Updated:** July 2026  
**Environment:** Development (Localhost:10000)

---

## Table of Contents

1. [Base Configuration](#base-configuration)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
   - [Auth Endpoints](#auth-endpoints)
   - [User Endpoints](#user-endpoints)
   - [V3 Endpoints](#v3-endpoints)
   - [Legacy Endpoints](#legacy-endpoints)

---

## Base Configuration

### API Base URL

**Development:**
```
http://localhost:10000
```

**Production:**
```
https://your-production-api.com
```

### Default Request Headers

```json
{
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

### Authentication Header (All Protected Endpoints)

```
Authorization: Bearer {access_token}
```

---

## Authentication

### Authentication Scheme

- **Type:** OAuth2 with JWT
- **Token Type:** Bearer Token
- **Algorithm:** HS256
- **Access Token Expiry:** 30 minutes
- **Refresh Token Expiry:** 7 days
- **Password Hashing:** bcrypt (12 rounds)

---

## API Endpoints

## AUTH ENDPOINTS

### 1. Register User

**Endpoint:** `POST /auth/register`

**Status Code:** `201 Created`

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "mobile_number": "+1234567890",
  "role": "Trader",
  "default_symbol": "BTCUSDT",
  "default_timeframe": "5m",
  "theme": "dark",
  "notification_settings": {
    "email_alerts": true,
    "push_notifications": true,
    "trade_notifications": true
  }
}
```

**Response (Success):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "user_123456",
  "full_name": "John Doe",
  "email": "john@example.com",
  "role": "Trader",
  "status": "active",
  "created_date": "2026-07-09T10:00:00",
  "message": "User created successfully"
}
```

**Response (Error - 400):**
```json
{
  "detail": "Email already exists"
}
```

**Response (Error - 422):**
```json
{
  "detail": "Invalid email format"
}
```

---

### 2. Login User

**Endpoint:** `POST /auth/login`

**Status Code:** `200 OK`

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "full_name": "John Doe",
    "email": "john@example.com",
    "role": "Trader",
    "default_symbol": "BTCUSDT",
    "default_timeframe": "5m"
  }
}
```

**Response (Error - 401):**
```json
{
  "detail": "Invalid email or password"
}
```

---

### 3. Refresh Access Token

**Endpoint:** `POST /auth/refresh`

**Status Code:** `200 OK`

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 1800
}
```

**Response (Error - 401):**
```json
{
  "detail": "Invalid refresh token"
}
```

---

### 4. Logout

**Endpoint:** `POST /auth/logout`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Request Body:** `{}` (empty)

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

### 5. Forgot Password

**Endpoint:** `POST /auth/forgot-password`

**Status Code:** `200 OK`

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Password reset instructions sent"
}
```

---

### 6. Reset Password

**Endpoint:** `POST /auth/reset-password`

**Status Code:** `200 OK`

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "token": "reset_token_from_email",
  "new_password": "NewSecurePassword123!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password reset successful"
}
```

---

### 7. Change Password

**Endpoint:** `POST /auth/change-password`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "current_password": "CurrentPassword123!",
  "new_password": "NewPassword123!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

## USER ENDPOINTS

### 1. Get Current User Profile

**Endpoint:** `GET /users/me`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Query Parameters:** None

**Request Body:** None

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "user_123456",
  "full_name": "John Doe",
  "email": "john@example.com",
  "mobile_number": "+1234567890",
  "role": "Trader",
  "status": "active",
  "created_date": "2026-07-09T10:00:00",
  "last_login": "2026-07-09T15:30:00",
  "default_symbol": "BTCUSDT",
  "default_timeframe": "5m",
  "theme": "dark",
  "notification_settings": {
    "email_alerts": true,
    "push_notifications": true
  }
}
```

---

### 2. Update User Profile

**Endpoint:** `PUT /users/me`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "full_name": "Jane Doe",
  "mobile_number": "+9876543210",
  "default_symbol": "ETHUSDT",
  "default_timeframe": "15m",
  "theme": "light",
  "notification_settings": {
    "email_alerts": false,
    "push_notifications": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated"
}
```

---

### 3. List All Users (Admin Only)

**Endpoint:** `GET /users`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {admin_token}"
}
```

**Query Parameters:** None

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "full_name": "John Doe",
    "email": "john@example.com",
    "role": "Trader",
    "status": "active",
    "created_date": "2026-07-09T10:00:00"
  },
  {
    "id": "507f1f77bcf86cd799439012",
    "full_name": "Jane Doe",
    "email": "jane@example.com",
    "role": "Trader",
    "status": "active",
    "created_date": "2026-07-09T10:05:00"
  }
]
```

---

### 4. Get User by ID (Admin Only)

**Endpoint:** `GET /users/{user_id}`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {admin_token}"
}
```

**Path Parameters:**
- `user_id` (string): User ID to retrieve

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "full_name": "John Doe",
  "email": "john@example.com",
  "mobile_number": "+1234567890",
  "role": "Trader",
  "status": "active",
  "created_date": "2026-07-09T10:00:00"
}
```

---

### 5. Update User (Admin Only)

**Endpoint:** `PUT /users/{user_id}`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {admin_token}",
  "Content-Type": "application/json"
}
```

**Path Parameters:**
- `user_id` (string): User ID to update

**Request Body:**
```json
{
  "full_name": "John Updated",
  "role": "Admin",
  "status": "inactive"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User updated"
}
```

---

### 6. Delete User (Admin Only)

**Endpoint:** `DELETE /users/{user_id}`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {admin_token}"
}
```

**Path Parameters:**
- `user_id` (string): User ID to delete

**Response:**
```json
{
  "success": true
}
```

---

## V3 ENDPOINTS

### 1. Dashboard Summary

**Endpoint:** `GET /v3/dashboard`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Query Parameters:** None

**Response:**
```json
{
  "account_balance": 100000.00,
  "today_pl": 2500.50,
  "open_trades": 3,
  "closed_trades": 47,
  "total_trades": 50,
  "win_rate": 68.5,
  "strategy_name": "Multi-EMA",
  "strategy_version": 2,
  "active_symbols": ["BTCUSDT", "ETHUSDT"],
  "portfolio_performance": {
    "daily_pnl": 2500.50,
    "weekly_pnl": 15000.00,
    "monthly_pnl": 45000.00,
    "ytd_pnl": 150000.00
  }
}
```

---

### 2. List Strategies

**Endpoint:** `GET /v3/strategies`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "strategy_name": "Multi-EMA",
    "version": 2,
    "enabled": true,
    "paper_mode": true,
    "live_mode": false,
    "symbol": "BTCUSDT",
    "timeframe": "5m",
    "created_date": "2026-07-01T10:00:00"
  },
  {
    "id": "507f1f77bcf86cd799439012",
    "strategy_name": "RSI-Bollinger",
    "version": 1,
    "enabled": false,
    "paper_mode": true,
    "live_mode": false,
    "symbol": "ETHUSDT",
    "timeframe": "15m",
    "created_date": "2026-06-15T10:00:00"
  }
]
```

---

### 3. Get Strategy Details

**Endpoint:** `GET /v3/strategies/{strategy_id}`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Path Parameters:**
- `strategy_id` (string): Strategy ID

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "strategy_name": "Multi-EMA",
  "version": 2,
  "enabled": true,
  "paper_mode": true,
  "live_mode": false,
  "priority": 1,
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "risk_percent": 1.0,
  "tp": 2.0,
  "sl": 1.0,
  "indicator_parameters": {
    "ema_fast": 12,
    "ema_slow": 26,
    "rsi_period": 14,
    "rsi_buy": 30,
    "rsi_sell": 70
  },
  "created_date": "2026-07-01T10:00:00",
  "last_updated": "2026-07-08T15:30:00"
}
```

---

### 4. Create Strategy

**Endpoint:** `POST /v3/strategies`

**Status Code:** `201 Created`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "strategy_name": "New Strategy",
  "version": 1,
  "enabled": true,
  "paper_mode": true,
  "live_mode": false,
  "priority": 1,
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "risk_percent": 1.0,
  "tp": 2.0,
  "sl": 1.0,
  "indicator_parameters": {
    "ema_fast": 12,
    "ema_slow": 26,
    "rsi_period": 14,
    "rsi_buy": 30,
    "rsi_sell": 70
  }
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439013",
  "strategy_name": "New Strategy",
  "version": 1,
  "enabled": true,
  "created_date": "2026-07-09T10:00:00"
}
```

---

### 5. Update Strategy

**Endpoint:** `PUT /v3/strategies/{strategy_id}`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}",
  "Content-Type": "application/json"
}
```

**Path Parameters:**
- `strategy_id` (string): Strategy ID

**Request Body:**
```json
{
  "enabled": false,
  "risk_percent": 1.5,
  "tp": 2.5
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "strategy_name": "Multi-EMA",
  "enabled": false,
  "risk_percent": 1.5,
  "last_updated": "2026-07-09T10:30:00"
}
```

---

### 6. Delete Strategy

**Endpoint:** `DELETE /v3/strategies/{strategy_id}`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Path Parameters:**
- `strategy_id` (string): Strategy ID

**Response:**
```json
{
  "success": true,
  "message": "Strategy deleted"
}
```

---

### 7. Run Backtest

**Endpoint:** `POST /v3/backtest/run`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "days": 365
}
```

**Response:**
```json
{
  "backtest_id": "507f1f77bcf86cd799439014",
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "days": 365,
  "status": "completed",
  "metrics": {
    "total_trades": 247,
    "wins": 169,
    "losses": 78,
    "win_rate": 68.4,
    "total_profit": 45000.00,
    "sharpe_ratio": 1.85,
    "max_drawdown": 12.5,
    "profit_factor": 2.1
  },
  "created_date": "2026-07-09T10:00:00",
  "completed_date": "2026-07-09T10:15:00"
}
```

---

### 8. Get Backtest by ID

**Endpoint:** `GET /v3/backtest/{backtest_id}`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Path Parameters:**
- `backtest_id` (string): Backtest ID

**Response:**
```json
{
  "backtest_id": "507f1f77bcf86cd799439014",
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "days": 365,
  "status": "completed",
  "metrics": {
    "total_trades": 247,
    "wins": 169,
    "losses": 78,
    "win_rate": 68.4,
    "total_profit": 45000.00,
    "sharpe_ratio": 1.85,
    "max_drawdown": 12.5,
    "profit_factor": 2.1
  }
}
```

---

### 9. List Backtests

**Endpoint:** `GET /v3/backtest/history`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
[
  {
    "backtest_id": "507f1f77bcf86cd799439014",
    "symbol": "BTCUSDT",
    "timeframe": "5m",
    "status": "completed",
    "win_rate": 68.4,
    "total_profit": 45000.00,
    "created_date": "2026-07-09T10:00:00"
  },
  {
    "backtest_id": "507f1f77bcf86cd799439015",
    "symbol": "ETHUSDT",
    "timeframe": "15m",
    "status": "completed",
    "win_rate": 65.2,
    "total_profit": 28000.00,
    "created_date": "2026-07-08T10:00:00"
  }
]
```

---

### 10. Delete Backtest

**Endpoint:** `DELETE /v3/backtest/{backtest_id}`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Path Parameters:**
- `backtest_id` (string): Backtest ID

**Response:**
```json
{
  "success": true
}
```

---

### 11. Paper Trading - Start

**Endpoint:** `POST /v3/paper/start`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Request Body:** `{}` (empty)

**Response:**
```json
{
  "success": true,
  "message": "Paper trading started",
  "initial_balance": 100000.00,
  "started_date": "2026-07-09T10:00:00"
}
```

---

### 12. Paper Trading - Stop

**Endpoint:** `POST /v3/paper/stop`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Request Body:** `{}` (empty)

**Response:**
```json
{
  "success": true,
  "message": "Paper trading stopped"
}
```

---

### 13. Paper Trading - Status

**Endpoint:** `GET /v3/paper/status`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "status": "active",
  "started_date": "2026-07-09T10:00:00",
  "current_balance": 102500.50,
  "initial_balance": 100000.00,
  "daily_pl": 2500.50
}
```

---

### 14. Paper Trading - Open Trades

**Endpoint:** `GET /v3/paper/open`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439020",
    "symbol": "BTCUSDT",
    "timeframe": "5m",
    "strategy_name": "Multi-EMA",
    "signal": "BUY",
    "entry_price": 42500.00,
    "current_price": 42750.00,
    "stop_loss": 42200.00,
    "target_price": 43500.00,
    "confidence": 85,
    "status": "OPEN",
    "pnl": 750.00,
    "pnl_percent": 1.76,
    "entry_time": "2026-07-09T10:00:00",
    "market_regime": "UPTREND"
  },
  {
    "id": "507f1f77bcf86cd799439021",
    "symbol": "ETHUSDT",
    "timeframe": "15m",
    "strategy_name": "RSI-Bollinger",
    "signal": "BUY",
    "entry_price": 2250.00,
    "current_price": 2280.00,
    "stop_loss": 2200.00,
    "target_price": 2350.00,
    "confidence": 72,
    "status": "OPEN",
    "pnl": 600.00,
    "pnl_percent": 2.67,
    "entry_time": "2026-07-09T09:30:00",
    "market_regime": "UPTREND"
  }
]
```

---

### 15. Paper Trading - Trade History

**Endpoint:** `GET /v3/paper/history`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Query Parameters:**
- `limit` (integer, optional): Number of trades to return (default: 100)

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439022",
    "symbol": "BTCUSDT",
    "timeframe": "5m",
    "strategy_name": "Multi-EMA",
    "signal": "BUY",
    "entry_price": 42000.00,
    "exit_price": 42500.00,
    "stop_loss": 41700.00,
    "target_price": 42500.00,
    "confidence": 80,
    "status": "CLOSED",
    "pnl": 1000.00,
    "pnl_percent": 2.38,
    "result": "WIN",
    "entry_time": "2026-07-08T15:00:00",
    "exit_time": "2026-07-08T16:30:00",
    "market_regime": "UPTREND"
  }
]
```

---

### 16. Paper Trading - Statistics

**Endpoint:** `GET /v3/paper/statistics`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "total_trades": 50,
  "open_trades": 3,
  "closed_trades": 47,
  "wins": 32,
  "losses": 15,
  "win_rate": 68.1,
  "average_win": 1562.50,
  "average_loss": -520.00,
  "profit_factor": 2.15,
  "total_profit": 45000.00,
  "total_loss": -7800.00,
  "net_profit": 37200.00,
  "current_balance": 137200.00,
  "initial_balance": 100000.00,
  "max_drawdown": 12.5,
  "sharpe_ratio": 1.85
}
```

---

### 17. List Brokers

**Endpoint:** `GET /v3/brokers`

**Status Code:** `200 OK`

**Required Headers:** None (Public endpoint)

**Response:**
```json
[
  {
    "broker_name": "Binance",
    "api_type": "REST",
    "supported": true,
    "features": ["Paper Trading", "Live Trading", "Margin Trading"]
  },
  {
    "broker_name": "Kucoin",
    "api_type": "REST",
    "supported": true,
    "features": ["Paper Trading", "Live Trading"]
  }
]
```

---

### 18. Connect Broker

**Endpoint:** `POST /v3/broker/connect`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "broker": "Binance",
  "api_key": "your_api_key_here",
  "secret_key": "your_secret_key_here"
}
```

**Response:**
```json
{
  "success": true,
  "broker": "Binance",
  "message": "Broker connected successfully",
  "connected_date": "2026-07-09T10:00:00"
}
```

---

### 19. Test Broker Connection

**Endpoint:** `POST /v3/broker/test`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "broker": "Binance",
  "api_key": "test_api_key",
  "secret_key": "test_secret_key"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Connection test passed",
  "account_balance": 1000000.00,
  "test_date": "2026-07-09T10:00:00"
}
```

---

### 20. Disconnect Broker

**Endpoint:** `POST /v3/broker/disconnect`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "broker": "Binance"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Broker disconnected"
}
```

---

### 21. Reports - Dashboard

**Endpoint:** `GET /v3/reports/dashboard`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "total_trades": 50,
  "win_rate": 68.1,
  "total_profit": 45000.00,
  "average_trade_duration": "2h 15m",
  "best_trade": 5000.00,
  "worst_trade": -1200.00,
  "top_symbols": ["BTCUSDT", "ETHUSDT"],
  "monthly_performance": [
    {
      "month": "June",
      "profit": 15000.00,
      "trades": 20
    },
    {
      "month": "July",
      "profit": 30000.00,
      "trades": 30
    }
  ]
}
```

---

### 22. Reports - Daily

**Endpoint:** `GET /v3/reports/daily`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
[
  {
    "date": "2026-07-09",
    "trades": 5,
    "wins": 3,
    "losses": 2,
    "profit": 2500.50,
    "win_rate": 60.0
  },
  {
    "date": "2026-07-08",
    "trades": 4,
    "wins": 3,
    "losses": 1,
    "profit": 1800.00,
    "win_rate": 75.0
  }
]
```

---

### 23. Reports - Monthly

**Endpoint:** `GET /v3/reports/monthly`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
[
  {
    "month": "2026-07",
    "trades": 50,
    "wins": 34,
    "losses": 16,
    "profit": 30000.00,
    "win_rate": 68.0
  },
  {
    "month": "2026-06",
    "trades": 45,
    "wins": 30,
    "losses": 15,
    "profit": 25000.00,
    "win_rate": 66.7
  }
]
```

---

### 24. Reports - Yearly

**Endpoint:** `GET /v3/reports/yearly`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
[
  {
    "year": 2026,
    "trades": 247,
    "wins": 169,
    "losses": 78,
    "profit": 150000.00,
    "win_rate": 68.4
  }
]
```

---

### 25. Reports - Equity Curve

**Endpoint:** `GET /v3/reports/equity`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "initial_balance": 100000.00,
  "equity_curve": [
    {
      "date": "2026-07-01",
      "balance": 100000.00,
      "cumulative_pnl": 0.00
    },
    {
      "date": "2026-07-02",
      "balance": 102500.00,
      "cumulative_pnl": 2500.00
    },
    {
      "date": "2026-07-03",
      "balance": 101800.00,
      "cumulative_pnl": 1800.00
    },
    {
      "date": "2026-07-09",
      "balance": 150000.00,
      "cumulative_pnl": 50000.00
    }
  ]
}
```

---

### 26. Reports - Performance

**Endpoint:** `GET /v3/reports/performance`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "total_trades": 50,
  "win_rate": 68.1,
  "profit_factor": 2.15,
  "sharpe_ratio": 1.85,
  "sortino_ratio": 2.45,
  "max_drawdown": 12.5,
  "recovery_factor": 4.0,
  "ulcer_index": 3.2,
  "cagr": 150.0,
  "volatility": 18.5,
  "symbol_performance": {
    "BTCUSDT": {
      "trades": 30,
      "win_rate": 70.0,
      "profit": 30000.00
    },
    "ETHUSDT": {
      "trades": 20,
      "win_rate": 65.0,
      "profit": 20000.00
    }
  }
}
```

---

### 27. Learning History

**Endpoint:** `GET /v3/learning`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439030",
    "title": "Strategy Update v2.1",
    "strategy": "Multi-EMA",
    "version": 2,
    "created_date": "2026-07-09T10:00:00",
    "details": {
      "changes": ["Updated EMA periods", "Added RSI filter"],
      "performance_delta": 2.5,
      "trades_analyzed": 47
    }
  }
]
```

---

### 28. Latest Learning

**Endpoint:** `GET /v3/learning/latest`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439030",
  "title": "Strategy Update v2.1",
  "strategy": "Multi-EMA",
  "version": 2,
  "created_date": "2026-07-09T10:00:00",
  "details": {
    "changes": ["Updated EMA periods", "Added RSI filter"],
    "performance_delta": 2.5,
    "trades_analyzed": 47,
    "recommendation": "Deploy to live trading"
  }
}
```

---

### 29. Scheduler Jobs

**Endpoint:** `GET /v3/scheduler/jobs`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "market-scan",
      "name": "Market Scan",
      "interval": "5m",
      "last_run": "2026-07-09T10:05:00",
      "next_run": "2026-07-09T10:10:00",
      "status": "scheduled"
    },
    {
      "job_id": "nightly-analysis",
      "name": "Nightly Analysis",
      "interval": "daily",
      "last_run": "2026-07-09T00:00:00",
      "next_run": "2026-07-10T00:00:00",
      "status": "scheduled"
    }
  ]
}
```

---

### 30. Scheduler - Start

**Endpoint:** `POST /v3/scheduler/start`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Request Body:** `{}` (empty)

**Response:**
```json
{
  "success": true,
  "message": "Scheduler start requested."
}
```

---

### 31. Scheduler - Stop

**Endpoint:** `POST /v3/scheduler/stop`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Request Body:** `{}` (empty)

**Response:**
```json
{
  "success": true,
  "message": "Scheduler stop requested."
}
```

---

### 32. Get Settings

**Endpoint:** `GET /v3/settings`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "theme": "dark",
  "refresh_interval": 30,
  "notifications": true,
  "risk": 1.0,
  "default_symbol": "BTCUSDT",
  "default_timeframe": "5m"
}
```

---

### 33. Update Settings

**Endpoint:** `PUT /v3/settings`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "theme": "light",
  "refresh_interval": 60,
  "notifications": false,
  "risk": 2.0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Settings updated",
  "theme": "light",
  "refresh_interval": 60,
  "risk": 2.0
}
```

---

### 34. Get Account

**Endpoint:** `GET /v3/account`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "balance": 150000.00,
  "leverage": 1,
  "broker": "Binance",
  "risk_percent": 1.0,
  "max_open_trades": 5,
  "account_type": "PAPER",
  "account_status": "active"
}
```

---

### 35. Update Account

**Endpoint:** `PUT /v3/account`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "balance": 200000.00,
  "risk_percent": 1.5,
  "max_open_trades": 10
}
```

**Response:**
```json
{
  "success": true,
  "message": "Account updated",
  "balance": 200000.00,
  "risk_percent": 1.5,
  "max_open_trades": 10
}
```

---

### 36. Get Symbols

**Endpoint:** `GET /v3/symbols`

**Status Code:** `200 OK`

**Required Headers:** None (Public endpoint)

**Response:**
```json
[
  "BTCUSDT",
  "ETHUSDT",
  "BNBUSDT",
  "XRPUSDT",
  "ADAUSDT",
  "DOGEUSDT"
]
```

---

### 37. Get Timeframes

**Endpoint:** `GET /v3/timeframes`

**Status Code:** `200 OK`

**Required Headers:** None (Public endpoint)

**Response:**
```json
[
  "1m",
  "5m",
  "15m",
  "30m",
  "1h",
  "4h",
  "1d",
  "1w",
  "1M"
]
```

---

## LEGACY ENDPOINTS

### 1. Market Analysis

**Endpoint:** `GET /analysis`

**Status Code:** `200 OK`

**Query Parameters:**
- `symbol` (string): Trading symbol (default: BTCUSDT)
- `timeframe` (string): Timeframe (default: 5m)

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "signal": "BUY",
  "confidence": 85,
  "price": 42750.00,
  "indicators": {
    "ema_fast": 42600.00,
    "ema_slow": 42400.00,
    "rsi": 65.5,
    "macd": 125.50
  }
}
```

---

### 2. Paper Trades Dashboard

**Endpoint:** `GET /paper-trades`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "open_trades": 3,
  "closed_trades": 47,
  "wins": 32,
  "losses": 15,
  "win_rate": 68.1,
  "total_profit": 45000.00
}
```

---

### 3. Paper Trades History

**Endpoint:** `GET /paper-trades/history`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Query Parameters:**
- `limit` (integer): Number of trades to return (default: 100)

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439022",
    "symbol": "BTCUSDT",
    "signal": "BUY",
    "entry": 42000.00,
    "exit": 42500.00,
    "status": "CLOSED",
    "pnl": 1000.00,
    "pnl_percent": 2.38,
    "result": "WIN",
    "entry_time": "2026-07-08T15:00:00",
    "exit_time": "2026-07-08T16:30:00"
  }
]
```

---

### 4. Current Strategy

**Endpoint:** `GET /strategy`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "name": "Multi-EMA",
  "version": 2,
  "ema_fast": 12,
  "ema_slow": 26,
  "rsi_buy": 30,
  "rsi_sell": 70,
  "tp_percent": 2.0,
  "sl_percent": 1.0
}
```

---

### 5. Performance Dashboard

**Endpoint:** `GET /performance`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
{
  "total_trades": 50,
  "wins": 32,
  "losses": 15,
  "win_rate": 68.1,
  "total_profit": 45000.00,
  "sharpe_ratio": 1.85,
  "max_drawdown": 12.5,
  "daily_statistics": {
    "date": "2026-07-09",
    "trades": 5,
    "profit": 2500.50
  }
}
```

---

### 6. Learning Logs

**Endpoint:** `GET /learning-logs`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439030",
    "date": "2026-07-09T10:00:00",
    "strategy": "Multi-EMA",
    "version": 2,
    "performance": {
      "win_rate": 68.1,
      "wins": 32,
      "losses": 15,
      "total_trades": 47,
      "status": "ACTIVE"
    }
  }
]
```

---

### 7. Backtest

**Endpoint:** `GET /backtest`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Query Parameters:**
- `symbol` (string): Trading symbol (default: BTCUSDT)
- `timeframe` (string): Timeframe (default: 5m)
- `days` (integer): Number of days to backtest (default: 365)

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "days": 365,
  "total_trades": 247,
  "wins": 169,
  "losses": 78,
  "win_rate": 68.4,
  "total_profit": 45000.00,
  "sharpe_ratio": 1.85,
  "max_drawdown": 12.5
}
```

---

### 8. Backtest History

**Endpoint:** `GET /backtest/history`

**Status Code:** `200 OK`

**Required Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

**Response:**
```json
[
  {
    "symbol": "BTCUSDT",
    "timeframe": "5m",
    "win_rate": 68.4,
    "total_profit": 45000.00,
    "completed_date": "2026-07-09T10:15:00"
  },
  {
    "symbol": "ETHUSDT",
    "timeframe": "15m",
    "win_rate": 65.2,
    "total_profit": 28000.00,
    "completed_date": "2026-07-08T10:15:00"
  }
]
```

---

### 9. Scheduler Status

**Endpoint:** `GET /scheduler/status`

**Status Code:** `200 OK`

**Response:**
```json
{
  "status": "running",
  "uptime": "2h 30m",
  "jobs_queued": 5,
  "jobs_completed": 150
}
```

---

### 10. Scheduler Dashboard

**Endpoint:** `GET /scheduler/dashboard`

**Status Code:** `200 OK`

**Response:**
```json
{
  "jobs_total": 10,
  "jobs_running": 1,
  "jobs_queued": 5,
  "jobs_completed": 150,
  "jobs_failed": 2,
  "uptime": "2h 30m"
}
```

---

### 11. Run Market Cycle

**Endpoint:** `POST /scheduler/run-market`

**Status Code:** `200 OK`

**Request Body:** `{}` (empty)

**Response:**
```json
{
  "success": true,
  "message": "Market cycle initiated",
  "job_id": "market_123456",
  "started_date": "2026-07-09T10:00:00"
}
```

---

### 12. Run Nightly Cycle

**Endpoint:** `POST /scheduler/run-nightly`

**Status Code:** `200 OK`

**Request Body:** `{}` (empty)

**Response:**
```json
{
  "success": true,
  "message": "Nightly cycle initiated",
  "job_id": "nightly_123456",
  "started_date": "2026-07-09T00:00:00"
}
```

---

## Error Responses

### Common Error Status Codes

| Status Code | Error Message | Description |
|-------------|---------------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions (role-based access) |
| 404 | Not Found | Resource not found |
| 422 | Validation Error | Invalid data format |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Rate Limiting

- **Requests per minute:** 60 (per API key)
- **Requests per hour:** 1000 (per API key)

---

## Pagination

For endpoints returning lists, pagination can be controlled using:

- `limit` (integer): Number of items to return (default: 100, max: 500)
- `offset` (integer): Number of items to skip (default: 0)

Example:
```
GET /v3/strategies?limit=50&offset=100
```

---

## CORS Policy

All endpoints have CORS enabled:

- **Allow Origins:** `*` (All origins)
- **Allow Methods:** `GET, POST, PUT, DELETE, OPTIONS`
- **Allow Headers:** `Content-Type, Authorization`

---

## Webhook Integration

To set up webhooks for trade notifications:

**Contact Support** to enable webhook endpoints for real-time trade updates.

---

## Implementation Notes for UI Team

### 1. Token Storage
- Store `access_token` in secure storage (FlutterSecureStorage)
- Store `refresh_token` in secure storage for automatic token refresh

### 2. Token Refresh
- Implement automatic token refresh when access token expires (401 response)
- Use refresh endpoint before token expiration for seamless experience

### 3. Error Handling
- Always check HTTP status codes and `detail` field in error responses
- Display user-friendly error messages based on error codes
- Log error details for debugging

### 4. Loading States
- Show loading indicators during API calls
- Implement retry logic for failed requests
- Use pagination for large datasets

### 5. Caching
- Cache user profile data until logout
- Cache strategy list and backtest history with 5-minute expiry
- Implement pull-to-refresh for dashboard

### 6. Real-time Updates
- Poll dashboard endpoints every 30 seconds for updates
- Poll paper trading statistics every 10 seconds for live updates
- Use websockets (if implemented) for trade notifications

### 7. Offline Support
- Cache critical endpoints (strategies, symbols, timeframes)
- Disable trading operations when offline
- Sync pending changes when connection restored

---

## Contact & Support

For API issues or integration questions:
- **Email:** support@marketai.com
- **Documentation:** https://docs.marketai.com
- **Status Page:** https://status.marketai.com

---

**End of Documentation**
