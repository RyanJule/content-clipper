import { create } from 'zustand'

export const useStore = create(set => ({
  // Media state
  media: [],
  setMedia: media => set({ media }),
  addMedia: newMedia => set(state => ({ media: [...state.media, newMedia] })),
  removeMedia: id => set(state => ({ media: state.media.filter(m => m.id !== id) })),

  // Clips state
  clips: [],
  setClips: clips => set({ clips }),
  addClip: newClip => set(state => ({ clips: [...state.clips, newClip] })),
  updateClip: (id, updates) =>
    set(state => ({
      clips: state.clips.map(clip => (clip.id === id ? { ...clip, ...updates } : clip)),
    })),
  removeClip: id => set(state => ({ clips: state.clips.filter(c => c.id !== id) })),

  // Social posts state
  posts: [],
  setPosts: posts => set({ posts }),
  addPost: newPost => set(state => ({ posts: [...state.posts, newPost] })),
  updatePost: (id, updates) =>
    set(state => ({
      posts: state.posts.map(post => (post.id === id ? { ...post, ...updates } : post)),
    })),
  removePost: id => set(state => ({ posts: state.posts.filter(p => p.id !== id) })),

  // UI state
  sidebarOpen: true,
  toggleSidebar: () => set(state => ({ sidebarOpen: !state.sidebarOpen })),
}))