const fs = require('fs');
const content = `import { HashRouter } from 'react-router-dom';
import Layout from './components/Layout';

export default function App() {
  return (
    <HashRouter>
      <Layout />
    </HashRouter>
  );
}
`;
fs.writeFileSync('./src/App.tsx', content, 'utf8');
console.log('Written bytes:', Buffer.byteLength(content));
console.log('Verify:', fs.readFileSync('./src/App.tsx', 'utf8').length);
