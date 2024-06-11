import { create } from "zustand";

const useMarketDataStore = create((set) => ({
    data: {},
    actions: {
        updateMarketData: (data_point) => {
            set(state => {
                return ({ data: { ...state.data, [data_point.ticker]: data_point } })
            })
        },
    }
}))

export const useMarketData = () => useMarketDataStore(store => store.data);
export const useMarketDataActions = () => useMarketDataStore(store => store.actions);