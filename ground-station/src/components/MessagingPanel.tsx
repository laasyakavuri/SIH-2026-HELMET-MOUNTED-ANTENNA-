import { useState } from 'react';
import type { Message } from '../models/types';
import { helmetName } from '../models/constants';
import { fmtTime } from '../utils/format';

interface Props { helmetId: string; messages: Message[]; onSend: (text: string) => void; }

export default function MessagingPanel({ helmetId, messages, onSend }: Props) {
  const [text, setText] = useState('');
  const send = () => {
    const t = text.trim();
    if (!t) return;
    onSend(t);
    setText('');
  };

  return (
    <section className="panel">
      <div className="panel-h">
        <span>Messaging · {helmetName(helmetId)}</span>
        <span className="pill dim">{messages.length} MSG</span>
      </div>
      <div className="msg-list">
        {messages.length === 0 && <div className="empty">No messages yet.</div>}
        {messages.map((m) => (
          <div key={m.id} className={`msg ${m.direction}`}>
            <div className="msg-bubble">
              <div className="msg-text">{m.text}</div>
              <div className="msg-meta">
                {fmtTime(m.timestamp)} · {m.direction === 'gs_to_helmet' ? 'GS→HELMET' : 'HELMET→GS'} · {m.status.toUpperCase()}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="msg-input">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder={`Message ${helmetName(helmetId)}…`}
          maxLength={120}
        />
        <button className="btn" onClick={send}>SEND</button>
      </div>
    </section>
  );
}
