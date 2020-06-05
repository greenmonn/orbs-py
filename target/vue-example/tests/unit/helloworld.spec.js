import Vue from "vue";
import HelloWorld from "@/components/HelloWorld.vue";

describe("HelloWorld", () => {
    it("has a created hook", () => {
        expect(typeof HelloWorld.created).toBe("function");
    });

    it("sets the correct default data", () => {
        expect(typeof HelloWorld.data).toBe("function");
        const defaultData = HelloWorld.data();
        expect(defaultData.message).toBe("hello!");
    });

    it("correctly sets the message when created", () => {
        const vm = new Vue(HelloWorld).$mount();
        expect(vm.message).toBe("bye!");
    });

    it("renders the correct message", () => {
        const Constructor = Vue.extend(HelloWorld);
        const vm = new Constructor().$mount();
        expect(vm.$el.textContent).toBe("bye!");
    });
});
