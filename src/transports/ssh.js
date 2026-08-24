import { Client } from "ssh2";
const DEFAULT_CONNECT_TIMEOUT = 10000;
const DEFAULT_COMMAND_TIMEOUT = 20000;
export async function runSshCommand(target, command) {
    return new Promise((resolve, reject) => {
        const conn = new Client();
        const connectTimeout = target.connectTimeout ?? DEFAULT_CONNECT_TIMEOUT;
        const commandTimeout = target.commandTimeout ?? DEFAULT_COMMAND_TIMEOUT;
        const timer = setTimeout(() => {
            conn.end();
            reject(new Error(`SSH connection timeout after ${connectTimeout}ms`));
        }, connectTimeout);
        conn.on("ready", () => {
            clearTimeout(timer);
            const cmdTimer = setTimeout(() => {
                conn.end();
                reject(new Error(`SSH command timeout after ${commandTimeout}ms`));
            }, commandTimeout);
            conn.exec(command, (err, stream) => {
                if (err) {
                    clearTimeout(cmdTimer);
                    conn.end();
                    reject(err);
                    return;
                }
                let stdout = "";
                let stderr = "";
                stream.on("close", (code) => {
                    clearTimeout(cmdTimer);
                    conn.end();
                    if (code !== 0 && code !== null) {
                        reject(new Error(stderr || `Command failed with exit code ${code}`));
                    }
                    else {
                        resolve(stdout);
                    }
                });
                stream.on("data", (data) => {
                    stdout += data.toString();
                });
                stream.stderr.on("data", (data) => {
                    stderr += data.toString();
                });
            });
        });
        conn.on("error", (err) => {
            clearTimeout(timer);
            reject(new Error(`SSH connection failed: ${err.message}`));
        });
        const connectOptions = {
            host: target.host,
            port: target.port ?? 22,
            username: target.username,
            readyTimeout: connectTimeout,
        };
        if (target.privateKey) {
            connectOptions.privateKey = target.privateKey;
            if (target.passphrase)
                connectOptions.passphrase = target.passphrase;
        }
        else if (target.password) {
            connectOptions.password = target.password;
        }
        conn.connect(connectOptions);
    });
}
