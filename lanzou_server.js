const express = require('express');
const axios = require('axios');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

// 存储会话信息
let session = {
    cookies: {},
    isLoggedIn: false,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
};

// 调试日志函数
const debugLog = (message, data = null) => {
    console.log(`[${new Date().toISOString()}] ${message}`);
    if (data) {
        console.log('Data:', JSON.stringify(data, null, 2));
    }
};

// 生成安全的 User-Agent
const generateSafeUserAgent = (ua) => {
    const match = ua.match(/Chrome\/([0-9.]+)/);
    if (match) {
        return `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${match[1]} Safari/537.36`;
    }
    return ua;
};

// 登录接口
app.post('/api/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        debugLog('Login attempt', { username });

        // 第一步：获取登录页面
        const loginPageResponse = await axios.get('https://pc.woozooo.com/', {
            headers: {
                'User-Agent': session.userAgent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
        });

        // 提取必要的 cookies
        const cookies = loginPageResponse.headers['set-cookie'];
        const cookieString = cookies ? cookies.map(cookie => cookie.split(';')[0]).join('; ') : '';

        // 第二步：发送登录请求
        const response = await axios.post('https://pc.woozooo.com/ajaxm.php', {
            action: 'login',
            task: 'login',
            username,
            password
        }, {
            headers: {
                'User-Agent': session.userAgent,
                'Referer': 'https://pc.woozooo.com/',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://pc.woozooo.com',
                'X-Requested-With': 'XMLHttpRequest',
                'Cookie': cookieString
            }
        });

        debugLog('Login response', response.data);

        if (response.data.zt === 1) {
            // 保存所有 cookies
            session.cookies = response.headers['set-cookie'];
            session.isLoggedIn = true;
            debugLog('Login successful');
            res.json({ success: true, message: '登录成功' });
        } else {
            debugLog('Login failed', response.data);
            res.json({ success: false, message: response.data.info || '登录失败' });
        }
    } catch (error) {
        debugLog('Login error', error.message);
        res.json({ success: false, message: error.message });
    }
});

// 获取文件夹列表接口
app.get('/api/folders', async (req, res) => {
    try {
        if (!session.isLoggedIn) {
            debugLog('Not logged in');
            return res.json({ success: false, message: '未登录' });
        }

        debugLog('Fetching folders');
        
        // 构建 cookie 字符串
        const cookieString = session.cookies.map(cookie => cookie.split(';')[0]).join('; ');
        
        // 获取文件夹列表
        const response = await axios.get('https://pc.woozooo.com/doupload.php', {
            params: {
                task: '47',
                folder_id: '-1',
                pg: '1',
                t: Date.now()
            },
            headers: {
                'User-Agent': session.userAgent,
                'Referer': 'https://pc.woozooo.com/mydisk.php',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Cookie': cookieString
            }
        });

        debugLog('Folders response headers', response.headers);
        debugLog('Folders response data', response.data);

        if (response.data.zt === 1) {
            const folders = response.data.text.map(folder => ({
                name: folder.name,
                fol_id: folder.fol_id,
                pid: folder.pid
            }));
            res.json({ success: true, data: folders });
        } else {
            res.json({ success: false, message: response.data.info || '获取文件夹列表失败' });
        }
    } catch (error) {
        debugLog('Folders error', error.message);
        if (error.response) {
            debugLog('Error response data', error.response.data);
            debugLog('Error response headers', error.response.headers);
        }
        res.json({ success: false, message: error.message });
    }
});

// 获取文件列表接口
app.get('/api/files', async (req, res) => {
    try {
        if (!session.isLoggedIn) {
            debugLog('Not logged in');
            return res.json({ success: false, message: '未登录' });
        }

        const { folder_id = '' } = req.query;
        debugLog('Fetching files', { folder_id });

        // 构建 cookie 字符串
        const cookieString = session.cookies.map(cookie => cookie.split(';')[0]).join('; ');
        
        // 获取文件列表
        const response = await axios.get('https://pc.woozooo.com/doupload.php', {
            params: {
                task: '5',
                folder_id,
                pg: '1',
                showempty: '0',
                t: Date.now()
            },
            headers: {
                'User-Agent': session.userAgent,
                'Referer': 'https://pc.woozooo.com/mydisk.php',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Cookie': cookieString
            }
        });

        debugLog('Files response headers', response.headers);
        debugLog('Files response data', response.data);

        if (response.data.zt === 1) {
            const files = response.data.text.map(file => ({
                name: file.name_all,
                id: file.id,
                size: file.size,
                time: file.time,
                downs: file.downs,
                is_folder: file.folder_id !== '-1'
            }));
            res.json({ success: true, data: files });
        } else {
            res.json({ success: false, message: response.data.info || '获取文件列表失败' });
        }
    } catch (error) {
        debugLog('Files error', error.message);
        if (error.response) {
            debugLog('Error response data', error.response.data);
            debugLog('Error response headers', error.response.headers);
        }
        res.json({ success: false, message: error.message });
    }
});

// 健康检查接口
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'ok',
        isLoggedIn: session.isLoggedIn,
        timestamp: new Date().toISOString()
    });
});

const PORT = 3000;
app.listen(PORT, () => {
    debugLog(`Server is running on port ${PORT}`);
}); 