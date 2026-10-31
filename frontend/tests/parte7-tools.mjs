import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
// Permite herramientas temporales sin instalar paquetes dentro de otros worktrees.
export async function tool(name) {
  const require = createRequire(process.env.MONITOR_TEST_NODE_MODULES
    ? resolve(process.env.MONITOR_TEST_NODE_MODULES, 'package.json') : import.meta.url);
  const loaded = await import(pathToFileURL(require.resolve(name)).href);
  return { ...(loaded.default || {}), ...loaded };
}
