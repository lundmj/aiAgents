/*
Enhanced styling for the React Todo App using Tailwind CSS.
*/

import { useEffect, useState, useRef } from 'react';

const STORAGE_KEY = 'todo_app_v1';

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

export default function App() {
  const [todos, setTodos] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  });

  const [text, setText] = useState('');
  const [filter, setFilter] = useState('all'); // all | active | completed
  const [editingId, setEditingId] = useState(null);
  const [editingText, setEditingText] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
    } catch (e) {
      // ignore
    }
  }, [todos]);

  const addTodo = (e) => {
    e.preventDefault();
    const value = text.trim();
    if (!value) return;
    const newTodo = { id: uid(), text: value, completed: false, createdAt: Date.now() };
    setTodos((t) => [newTodo, ...t]);
    setText('');
    inputRef.current?.focus();
  };

  const toggle = (id) => {
    setTodos((t) => t.map((it) => (it.id === id ? { ...it, completed: !it.completed } : it)));
  };

  const remove = (id) => {
    setTodos((t) => t.filter((it) => it.id !== id));
  };

  const startEdit = (id, currentText) => {
    setEditingId(id);
    setEditingText(currentText);
  };

  const commitEdit = (id) => {
    const trimmed = editingText.trim();
    if (!trimmed) {
      // delete if edit cleared
      remove(id);
    } else {
      setTodos((t) => t.map((it) => (it.id === id ? { ...it, text: trimmed } : it)));
    }
    setEditingId(null);
    setEditingText('');
  };

  const clearCompleted = () => {
    setTodos((t) => t.filter((it) => !it.completed));
  };

  const filtered = todos.filter((it) => {
    if (filter === 'active') return !it.completed;
    if (filter === 'completed') return it.completed;
    return true;
  });

  const remaining = todos.filter((t) => !t.completed).length;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-50 to-blue-100 p-6">
      <div className="w-full max-w-2xl bg-white shadow-lg rounded-lg overflow-hidden">
        <header className="bg-blue-600 text-white p-4">
          <h1 className="text-2xl font-bold">Todo App</h1>
          <p className="text-sm">Organize your tasks efficiently</p>
        </header>

        <main className="p-6">
          <form onSubmit={addTodo} className="flex gap-4 mb-6">
            <input
              id="new-todo"
              ref={inputRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="What needs to be done?"
            />
            <button
              type="submit"
              className="px-6 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
              disabled={!text.trim()}
            >
              Add
            </button>
          </form>

          <div className="flex items-center justify-between mb-4">
            <div className="flex gap-2" role="tablist" aria-label="Filter todos">
              {['all', 'active', 'completed'].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-2 rounded-md text-sm font-medium ${filter === f ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                  role="tab"
                  aria-selected={filter === f}
                >
                  {f[0].toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>

            <div className="text-sm text-gray-600">{remaining} tasks left</div>
          </div>

          <ul className="space-y-4">
            {filtered.length === 0 && (
              <li className="text-center text-gray-500">No tasks available. Add a new one above!</li>
            )}

            {filtered.map((todo) => (
              <li key={todo.id} className="flex items-center gap-4 bg-gray-50 p-4 rounded-md shadow-sm">
                <input
                  type="checkbox"
                  checked={todo.completed}
                  onChange={() => toggle(todo.id)}
                  className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  aria-label={`Mark ${todo.text} as ${todo.completed ? 'incomplete' : 'complete'}`}
                />

                <div className="flex-1">
                  {editingId === todo.id ? (
                    <input
                      value={editingText}
                      onChange={(e) => setEditingText(e.target.value)}
                      onBlur={() => commitEdit(todo.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') commitEdit(todo.id);
                        if (e.key === 'Escape') {
                          setEditingId(null);
                          setEditingText('');
                        }
                      }}
                      autoFocus
                      className="w-full rounded-md border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
                    />
                  ) : (
                    <span
                      onDoubleClick={() => startEdit(todo.id, todo.text)}
                      className={`block ${todo.completed ? 'line-through text-gray-400' : 'text-gray-800'}`}
                    >
                      {todo.text}
                    </span>
                  )}
                </div>

                <button
                  onClick={() => remove(todo.id)}
                  className="text-red-500 hover:text-red-700"
                  aria-label={`Delete ${todo.text}`}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>

          <div className="mt-6 flex items-center justify-between">
            <div className="text-sm text-gray-600">Total tasks: {todos.length}</div>
            <div className="flex gap-2">
              <button
                onClick={() => setTodos((t) => t.map((it) => ({ ...it, completed: true })))}
                className="px-4 py-2 rounded-md bg-green-100 text-green-700 hover:bg-green-200"
              >
                Mark all done
              </button>
              <button
                onClick={() => setTodos((t) => t.map((it) => ({ ...it, completed: false })))}
                className="px-4 py-2 rounded-md bg-yellow-100 text-yellow-700 hover:bg-yellow-200"
              >
                Mark all active
              </button>
              <button
                onClick={clearCompleted}
                className="px-4 py-2 rounded-md bg-red-100 text-red-700 hover:bg-red-200"
              >
                Clear completed
              </button>
            </div>
          </div>
        </main>

        <footer className="bg-gray-100 text-center text-sm text-gray-500 p-4">
          Built with ❤️ using React and Tailwind CSS
        </footer>
      </div>
    </div>
  );
}
