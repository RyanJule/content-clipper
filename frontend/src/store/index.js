import { create } from 'zustand'
import { authService } from '../services/authService'

export const useStore = create(set => ({
  // Auth state
  user: authService.getCurrentUser(),
  isAuthenticated: authService.isLoggedIn(),
  setUser: user => set({ user, isAuthenticated: !!user }),
  logout: () => {
    authService.logout()
    set({
      user: null,
      isAuthenticated: false,
      brands: [],
      media: [],
      clips: [],
      posts: [],
      scheduledPosts: [],
      accounts: [],
      schedules: [],
      selectedBrandId: null,
      selectedAccountId: null,
    })
  },

  // Brands state
  brands: [],
  setBrands: brands => set({ brands }),
  addBrand: brand => set(state => ({ brands: [...state.brands, brand] })),
  updateBrand: (id, updates) =>
    set(state => ({
      brands: state.brands.map(b => (b.id === id ? { ...b, ...updates } : b)),
    })),
  removeBrand: id => set(state => ({ brands: state.brands.filter(b => b.id !== id) })),

  // Accounts state
  accounts: [],
  setAccounts: accounts => set({ accounts }),
  addAccount: account => set(state => ({ accounts: [...state.accounts, account] })),
  updateAccount: (id, updates) =>
    set(state => ({
      accounts: state.accounts.map(acc => (acc.id === id ? { ...acc, ...updates } : acc)),
    })),
  removeAccount: id => set(state => ({ accounts: state.accounts.filter(a => a.id !== id) })),

  // Schedules state
  schedules: [],
  setSchedules: schedules => set({ schedules }),
  addSchedule: schedule => set(state => ({ schedules: [...state.schedules, schedule] })),
  updateSchedule: (id, updates) =>
    set(state => ({
      schedules: state.schedules.map(sch => (sch.id === id ? { ...sch, ...updates } : sch)),
    })),
  removeSchedule: id => set(state => ({ schedules: state.schedules.filter(s => s.id !== id) })),

  // Calendar state
  calendarData: [],
  setCalendarData: data => set({ calendarData: data }),

  // Selected brand filter (drives account filtering across the app)
  selectedBrandId: null,
  setSelectedBrandId: id => set({ selectedBrandId: id, selectedAccountId: null }),

  // Selected account filter
  selectedAccountId: null,
  setSelectedAccountId: id => set({ selectedAccountId: id }),

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

  // Scheduled posts state
  scheduledPosts: [],
  setScheduledPosts: scheduledPosts => set({ scheduledPosts }),
  addScheduledPost: post => set(state => ({ scheduledPosts: [...state.scheduledPosts, post] })),
  updateScheduledPost: (id, updates) =>
    set(state => ({
      scheduledPosts: state.scheduledPosts.map(p => (p.id === id ? { ...p, ...updates } : p)),
    })),
  removeScheduledPost: id =>
    set(state => ({ scheduledPosts: state.scheduledPosts.filter(p => p.id !== id) })),

  // UI state
  sidebarOpen: true,
  toggleSidebar: () => set(state => ({ sidebarOpen: !state.sidebarOpen })),
}))