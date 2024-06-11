import { create } from "zustand";

const useToastStore = create((set) => ({
    toasts: [],
    actions: {
        addToast: (toast) => {
            set(state => {
                return ({ toasts: [...state.toasts, toast] })
            })
        },
        removeToast: (id) => {
            set(state => {
                return ({ toasts: state.toasts.filter(toast => toast.id !== id) });
            })
        },
        clearToasts: () => (set({ toasts: [] }))
    }
}))

export const useToasts = () => useToastStore(store=>store.toasts);
export const useToastActions = () => useToastStore(store=>store.actions);