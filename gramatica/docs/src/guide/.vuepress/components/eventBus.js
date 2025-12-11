import Vue from 'vue';

export const eventBus = new Vue({
    data: {
        eventQueue: [],
    },
    methods: {
        emit(event, ...args) {
            if (this._events && this._events[event]) {
                // If there are listeners for the event, emit it immediately
                this.$emit(event, ...args);
            } else {
                // Otherwise, queue the event
                this.eventQueue.push({ event, args });
            }
        },
        on(event, callback) {
            // Register the listener
            this.$on(event, callback);

            // Deliver any queued events
            this.eventQueue = this.eventQueue.filter(queuedEvent => {
                if (queuedEvent.event === event) {
                    this.$emit(event, ...queuedEvent.args);
                    return false;
                }
                return true;
            });
        },
    },
});