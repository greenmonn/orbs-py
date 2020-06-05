import Vue from "vue";
import HelloWorld_orbs from "@/components/HelloWorld_orbs.vue";

describe("HelloWorld_orbs", () => {
    it("has a created hook", () => {
        expect(typeof HelloWorld_orbs.created).toBe("function");
    });

    it("sets the correct default data", () => {
        expect(typeof HelloWorld_orbs.data).toBe("function");
        const defaultData = HelloWorld_orbs.data();
        expect(defaultData.message).toBe("hello!");
    });

    it("correctly sets the message when created", () => {
        const vm = new Vue(HelloWorld_orbs).$mount();
        expect(vm.message).toBe("bye!");
    });

    it("renders the correct message", () => {
        const Constructor = Vue.extend(HelloWorld_orbs);
        const vm = new Constructor().$mount();
        expect(vm.$el.textContent).toBe("bye!");
    });
});
