import { defineStore } from 'pinia'
import { getZones, getSpots } from '@/api/parking'

export const useParkingStore = defineStore('parking', {
    state: () => ({
        zones: [],
        spots: [],
        currentZoneId: null,
        loading: false
    }),

    getters: {
        currentZone: (state) => {
            return state.zones.find(z => z.zone_id === state.currentZoneId)
        },

        availableSpots: (state) => {
            return state.spots.filter(s => s.status === 0)
        },

        occupiedSpots: (state) => {
            return state.spots.filter(s => s.status === 1)
        },

        reservedSpots: (state) => {
            return state.spots.filter(s => s.status === 3)
        }
    },

    actions: {
        async fetchZones() {
            console.log('parkingStore: Fetching zones...');
            this.loading = true
            try {
                const res = await getZones()
                this.zones = res.data
                console.log(`parkingStore: Found ${this.zones.length} zones`);

                if (this.zones.length > 0 && !this.currentZoneId) {
                    this.currentZoneId = this.zones[0].zone_id
                }
            } catch (err) {
                console.error('parkingStore: fetchZones error', err);
            } finally {
                this.loading = false
            }
        },

        async fetchSpots(zoneId) {
            if (!zoneId) return;
            console.log(`parkingStore: Fetching spots for zone ${zoneId}...`);
            this.loading = true
            try {
                const res = await getSpots(zoneId)
                this.spots = res.data
                this.currentZoneId = zoneId
                console.log(`parkingStore: Loaded ${this.spots.length} spots`);
            } catch (err) {
                console.error('parkingStore: fetchSpots error', err);
            } finally {
                this.loading = false
            }
        },

        updateSpotStatus(spotId, status, currentPlate = null) {
            const spot = this.spots.find(s => s.spot_id === spotId)
            if (spot) {
                spot.status = status
                spot.current_plate = currentPlate
            }
        }
    }
})
