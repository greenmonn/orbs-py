// selenium + mocha test for target behavior + DOM Tree matching

// preserve visuals: compare DOM element (in interested area)
// preserve behaviors: compare difference in DOM element
const fs = require("fs");
const { Builder, By, Key, until } = require("selenium-webdriver");
const chrome = require("selenium-webdriver/chrome");

function findDiff(str1, str2) {
    let diff1 = "";
    let diff2 = "";
    str2.split("").forEach(function (val, i) {
        if (val != str1.charAt(i)) {
            diff1 += val;
            diff2 += str1.charAt(i);
        }
    });
    return [diff1, diff2];
}

async function recordTargetObject(driver, targetElement) {
    let outerHtml = await targetElement.getAttribute("outerHTML");
    let properties = await driver.executeScript(
        "return window.getComputedStyle(arguments[0], null);",
        targetElement
    );

    // Contains all children's information as well
    const targetObject = {
        html: outerHtml,
        cssProps: {},
        childProps: [],
    };

    // console.log(`${properties}`);
    for (let i = 0; i < properties.length; i++) {
        let value = await targetElement.getCssValue(properties[i]);
        // console.log(`${properties[i]}: ${value}`);
        targetObject.cssProps[properties[i]] = value;
    }

    const childrens = await targetElement.findElements(By.xpath(".//*"));

    console.log(`${childrens.length}`);
    for (let i = 0; i < childrens.length; i++) {
        let elem = childrens[i];
        let childHtml = await elem.getAttribute("outerHTML");
        // console.log(`${childHtml}`);
        let childProperties = await driver.executeScript(
            "return window.getComputedStyle(arguments[0], null);",
            elem
        );

        let child = {};
        for (let i = 0; i < childProperties.length; i++) {
            let value = await elem.getCssValue(childProperties[i]);
            // console.log(`${childProperties[i]}: ${value}`);
            child[childProperties[i]] = value;
        }

        targetObject.childProps.push(child);
    }

    return targetObject;
}

(async function checkMatch() {
    const screen = {
        width: 640,
        height: 480,
    };

    let driver = await new Builder()
        .forBrowser("chrome")
        .setChromeOptions(new chrome.Options().headless().windowSize(screen))
        .build();

    await driver.get("http://localhost:8080/intermediate_orbs.html");
    const targetElement = await driver.findElement(By.className("download"));
    // await targetElement.click();

    const targetObject = await recordTargetObject(driver, targetElement);

    const actions = driver.actions();
    await actions.move({ origin: targetElement }).perform();

    const targetObjectAfterAction = await recordTargetObject(
        driver,
        targetElement
    );

    // TODO: Need to be improved: save initial target element DOM and differences after
    // Currently, simply save initial and after event DOM state for the target element (do not catch outside changes)
    // If not use diff: should compare all DOM tree.. which is too costly
    // How to capture diff? we should be able to captre dom modification callback event

    const trajectory = {
        initial: targetObject,
        afterAction: targetObjectAfterAction,
    };

    // console.log(`${outerHtml}`);
    const current = JSON.stringify(trajectory);
    fs.readFile("targetElement.json", (err, reference) => {
        if (err) {
            console.log(err);
        }

        reference = reference.toString();

        if (current == reference) {
            console.log("[Criteria Match] Target element remains the same");
        } else {
            console.log("[Not Match] Target element changed");
            let diffs = findDiff(current, reference);
            // TODO: more smart diff function
            console.log(diffs[0]);
            console.log(diffs[1]);
        }
    });
})();
