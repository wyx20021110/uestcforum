# WebSocket服务器启动指南

## 简介

Django的开发服务器(`runserver`)不完全支持WebSocket。要使用WebSocket功能，需要使用支持ASGI的服务器，如Daphne。

## 启动WebSocket服务器

使用Daphne启动服务器非常简单。只需执行以下命令：

```bash
# 启动Daphne服务器
daphne -b 0.0.0.0 -p 8000 myproject.asgi:application
```

### 参数说明

- `-b 0.0.0.0`: 绑定到所有网络接口
- `-p 8000`: 使用8000端口（可以根据需要更改）
- `myproject.asgi:application`: ASGI应用入口点

## 重要提示

1. 使用Daphne启动服务器后，它将同时处理HTTP请求和WebSocket连接
2. 无需额外的Django开发服务器
3. 确保已安装Daphne：`pip install daphne`

## 常见问题

### Q: 需要修改前端代码吗？
A: 不需要。使用Daphne替代Django开发服务器后，前端代码不需要特别修改。WebSocket连接将使用与HTTP相同的主机和端口。

### Q: 如何在开发环境和生产环境之间切换？
A: 在开发环境中可以直接使用`daphne`命令，在生产环境中建议使用Supervisor或Systemd等工具管理Daphne进程。

### Q: 如何测试WebSocket连接是否正常？
A: 可以使用浏览器控制台或专门的WebSocket调试工具来验证连接，例如Chrome开发者工具的Network标签页。 