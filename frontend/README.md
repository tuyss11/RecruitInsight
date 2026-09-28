# RecruitInsight Frontend

Vue 3 + Vite 单页招聘模拟数据分析 Dashboard，通过 Axios 调用 Spring Boot API，并使用 ECharts 展示技能、城市、岗位类别与月薪统计。

## 本地运行

先启动监听 `localhost:8080` 的 Spring Boot 后端，然后执行：

```powershell
cd frontend
npm install
npm run dev
```

浏览器访问 `http://127.0.0.1:5173`。Vite 将 `/api` 请求代理到 `http://localhost:8080`，无需在后端开放全局 CORS。

## 构建

```powershell
npm run build
```

所有页面统计结果均来自项目模拟数据，仅用于功能演示。
