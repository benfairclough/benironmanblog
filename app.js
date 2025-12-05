// app.js
const express = require('express');
const path = require('path');
const fs = require('fs/promises');

const POSTS_DIR = process.env.POSTS_DIR || path.join(__dirname,'data');
const POSTS_FILE = path.join(POSTS_DIR,'posts.json');

async function ensureDir(){
  await fs.mkdir(POSTS_DIR,{recursive:true});
  try{ await fs.access(POSTS_FILE); } catch { await fs.writeFile(POSTS_FILE,'[]'); }
}
async function readPosts(){ return JSON.parse(await fs.readFile(POSTS_FILE,'utf8')||'[]'); }
async function writePosts(posts){
  const tmp = POSTS_FILE + '.tmp';
  await fs.writeFile(tmp, JSON.stringify(posts,null,2));
  await fs.rename(tmp, POSTS_FILE);
}

const app = express();
app.use(express.json());

// API endpoints
app.get('/api/posts', async (req,res)=>{ await ensureDir(); res.json(await readPosts()); });
app.post('/api/posts', async (req,res)=>{
  const {title,body} = req.body; if(!title||!body) return res.status(400).json({error:'title and body required'});
  await ensureDir();
  const posts = await readPosts();
  const post = { id: Date.now().toString(), title, body, created: Date.now(), comments: [] };
  posts.push(post); await writePosts(posts); res.status(201).json(post);
});
app.post('/api/posts/:id/comments', async (req,res)=>{
  const {id} = req.params; const {name,text} = req.body; if(!text) return res.status(400).json({error:'text required'});
  await ensureDir(); const posts = await readPosts();
  const p = posts.find(x=>x.id===id); if(!p) return res.status(404).json({error:'post not found'});
  p.comments.push({name:name||'Anonymous',text,when:Date.now()}); await writePosts(posts); res.status(201).json(p);
});

// Health check for readiness
app.get('/health', (req,res)=>res.json({ok:true}));

// Listen on internal port 3000 (nginx will proxy to this)
const port = process.env.PORT || 3000;
app.listen(port, ()=>console.log(`Node API listening on ${port}`));
