/**
 * Naive implementation of react-like library
 */

const isEvent = key => key.startsWith("on");
const isProperty = key => key !== "children" && !isEvent(key);
const isNew = (prev, next) => key => prev[key] !== next[key];
const isGone = (prev, next) => key => !(key in next);
const camelToCSS = (str) => str.replace(/[A-Z]/g, letter => `-${letter.toLowerCase()}`);
const objectToCSS = (obj) => Object.entries(obj)
  .map(([key, value]) => `${camelToCSS(key)}: ${value}`)
  .join('; ');

class FiberNode {
  /**
   * 
   * @param {string | Function} type 
   * @param {object} props 
   * @param  {...FiberNode} children
   * @returns {FiberNode}
   */
  constructor(type, props) {
    this.type = type;
    this.props = props || {};
    this.props.children = this.props.children || [];
    this.dom = null;
    this.key = 0;
    this.old = null;
    this.parent = null;
    this.effect = null;
    this.states = [];
    this.effects = [];
    this.stId = 0;
  }
  get child() {
    return this.props.children && this.props.children[0] || null;
  }
  set child(val) {
    this.props.children[0] = val;
  }
  get children() {
    return this.props && this.props.children || null;
  }
  set children(val) {
    if (!this.props) this.props = {};
    this.props.children = val;
  }
  get sibling() {
    return this.parent && this.parent.children && this.parent.children[this.key + 1] || null;
  }
  set sibling(val) {
    if (this.parent) {
      val.key = this.key + 1;
      this.parent.children[this.key + 1] = val;
    }
  }
  getNameSpace() {
    if (this.type === 'svg') {
      if ('xmlns' in this.props)
        return (this.props.xmlns);
      return null;
    }
    if (this.parent)
      return this.parent.getNameSpace();
    return null;
  }
  setKey(key) {
    this.key = key;
    return this;
  }
  parentsSiblings() {
    if (!this.children) return;
    this.children.forEach((child, idx) => {
      child.parent = this;
      child.key = idx;
      if (child instanceof FiberNode)
        child.parentsSiblings();
    });
  }
  resolveFunc(ftReact) {
    this.stId = 0;
    ftReact._currentNode = this;
    //const oldChildren = this.children;
    const children = this.type(this.props);
    //console.log("RESOLVE: ", this.type.name, oldChildren, children);
    ftReact._currentNode = null;
    this.children = Array.isArray(children) ? children : [children];
    this.parentsSiblings();
  }
  clone() {
    const clonedProps = {
      ...this.props,
      children: this.children.map(child => child instanceof FiberNode ? child.clone() : child)
    };
    const clonedNode = new FiberNode(this.type, clonedProps);
    clonedNode.dom = this.dom;
    clonedNode.states = this.states ? [...this.states] : [];
    clonedNode.effects = this.effects ? [...this.effects] : [];
    clonedNode.key = this.key;
    clonedNode.parent = this.parent;
    return clonedNode;
  }

  /**
   * @param {FiberNode[]} children
   */
  reconcile(children, ftReact) {
    //console.log("  VNode.reconcile RECONCILE: ", this, this.old);
    //this.type instanceof Function && console.log("RECONCILE: ", this.type.name, this.old?.type.name, this);
    let prevSibling = null;
    let oldNode = this.old && this.old.child;
    let i = 0;
    while (i < children.length) {
      const el = children[i];
      let newNode = null;
      let sameType = oldNode && el && oldNode.type == el.type;
      if (sameType) {
        newNode = new FiberNode(oldNode.type, el.props);
        newNode.dom = oldNode.dom;
        newNode.parent = this;
        newNode.old = oldNode;
        newNode.states = oldNode.states;
        newNode.effect = "UPDATE";
      }
      if (el && !sameType) {
        newNode = new FiberNode(el.type, el.props);
        newNode.parent = this;
        newNode.states = el.states;
        newNode.effect = "PLACEMENT";
      }
      if (oldNode && !sameType) {
        oldNode.effect = "DELETION";
        ftReact._deletions.push(oldNode);
      }
      if (oldNode) {
        oldNode = oldNode.sibling;
      }
      if (i === 0) {
        this.child = newNode;
      } else if (el && el.type) {
        prevSibling.sibling = newNode;
      }
      prevSibling = newNode;
      i++;
    }
    while (oldNode) {
      oldNode.effect = "DELETION";
      ftReact._deletions.push(oldNode);
      oldNode = oldNode.sibling;
    }
  }
  commit() {
    // console.log("  VNode.commit ", this);
    //this.type instanceof Function && console.log("COMMIT: ", this.type.name, this);
    let domParentNode = this.parent;
    while (!domParentNode.dom) {
      domParentNode = domParentNode.parent;
    }
    const domParent = domParentNode.dom;
    if (this.effect === "PLACEMENT" && this.dom != null)
      domParent.appendChild(this.dom);
    else if (this.effect === "UPDATE" && this.dom != null)
      this.updateDom();
    else if (this.effect === "DELETION")
      this.delete(domParent);
    this.effect = null;
    this.old = this.clone();
    this.child && this.child.commit();
    this.sibling && this.sibling.commit();
  }
  delete(domParent) {
    //console.log("  VNode.delete", this, domParent);
    if (this.dom && domParent.contains(this.dom)) {
      domParent.removeChild(this.dom);
    } else {
      this.child && this.child.delete(domParent);
    }
    if (this.effects) {
      this.effects.forEach(effect => {
          if (effect && effect.cleanup) {
            effect.cleanup();
          }
      });
    };
  }
  update(ftReact) {
    //console.log("  VNode.update", this);
    //this.type instanceof Function && console.log("UPDATE: ", this.type.name, this.old?.type.name, this);
    if (this.type instanceof Function) this.resolveFunc(ftReact); else if (!this.dom) this.createDom();
    this.reconcile(this.children, ftReact);
  }
  createDom() {
    //console.log("  VNode.createDom", this);
    if (this.type == "TEXT_ELEMENT")
      this.dom = document.createTextNode("");
    else {
      const nameSpace = this.getNameSpace();
      this.dom = nameSpace
        ? document.createElementNS(nameSpace, this.type)
        : document.createElement(this.type);
    }
    this.updateDom();
  }
  updateDom = () => {
    //console.log("  VNode.updateDom", this);
    const oldProps = this.old && this.old.props || {};
    //Remove old or changed event listeners
    Object.keys(oldProps).filter(isEvent).filter(key => !(key in this.props) || isNew(oldProps, this.props)(key)).forEach(name => {
      const eventType = name.toLowerCase().substring(2);
      //console.log("     removeEventListener", this.dom.tagName || this.type, name, eventType);
      this.dom.removeEventListener(eventType, oldProps[name]);
    });

    // Remove old properties
    Object.keys(oldProps).filter(isProperty).filter(isGone(oldProps, this.props)).forEach(name => {
      //console.log("     removeProperties", this.dom.tagName || this.type, name);
      this.dom[name] = "";
    });

    // Set new or changed properties
    Object.keys(this.props).filter(isProperty).filter(isNew(oldProps, this.props)).forEach(name => {
      //console.log("     setProperties", this.dom.tagName || this.type, name, this.props[name]);
      if (this.getNameSpace()) {
        this.dom.setAttribute(name, this.props[name])
      } else {
        if (name === 'style' && typeof this.props[name] === 'object') {
          this.dom[name] = objectToCSS(this.props[name]);
        } else if (name === 'className') {
          this.dom[name] = this.props[name];
        } else {
          if (this.dom instanceof Element) {
            if (this.props[name] || typeof this.props[name] !== 'boolean')
              this.dom.setAttribute(name, this.props[name])
          } else {
            this.dom[name] = this.props[name];
          }
        }
      }
    });

    // Add event listeners
    Object.keys(this.props).filter(isEvent).filter(isNew(oldProps, this.props)).forEach(name => {
      const eventType = name.toLowerCase().substring(2);
      //console.log("     addEventListener", this.dom.tagName || this.type, name, eventType);
      this.dom.addEventListener(eventType, this.props[name]);
    });
  };
}
class FTReact {
  constructor() {
    /** @private */
    this._root = new FiberNode("ROOT_ELEMENT", {});
    /** @private */
    this._nextTask = null;
    /** @private */
    this._deletions = [];
    /** @private */
    this._renderLoop = this._renderLoop.bind(this);
    /** @private */
    this._newChanges = false;
    /** @private */
    this._currentNode = null;
    /** @private */
    this._updateQueue = [];
  }

  /** @private */
  _scheduleUpdate(component) {
    if (!this._updateQueue.includes(component)) {
      this._updateQueue.push(component);
    }
  }

  /** @private */
  _commit() {
    //console.log("FTReact.commit");
    this._deletions.forEach(el => el.commit());
    this._deletions = [];
    this._root.child && this._root.child.commit();
    this._runEffects();
    this._newChanges = false;
  }
  /** @private */
  _getNextNode(node) {
    if (node.child)
      return node.child;
    while (node) {
      if (node.sibling)
        return node.sibling;
      node = node.parent;
    }
    return null;
  }
  /** @private */
  _setNextTask() {
    if (this._nextTask) {
      const nextNode = this._getNextNode(this._nextTask);
      if (nextNode && this._updateQueue.includes(nextNode))
          this._updateQueue = this._updateQueue.filter(it => it !== nextNode);
      if (nextNode) {
        this._nextTask = nextNode;
        return ;
      }
    }
    this._nextTask = this._updateQueue.shift() || null;
  }

  /** @private */
  _renderLoop(deadline) {
    let shouldYield = false;
    this._setNextTask();
    while (this._nextTask && !shouldYield) {
      this._nextTask.update(this);
      this._newChanges = true;
      this._setNextTask();
      shouldYield = deadline.timeRemaining() < 1;
    }
    if (!this._nextTask && this._newChanges) {
      this._commit();
    }
    requestIdleCallback(this._renderLoop);
  }
  useState(initialValue) {
    const node = this._currentNode;
    const oldHook = node.old && node.old.states[node.stId];
    const hook = {
      state: oldHook ? oldHook.state : initialValue,
      queue: []
    };
    const actions = oldHook ? oldHook.queue : [];
    actions.forEach(action => {
      hook.state = action instanceof Function ? action(hook.state) : action;
    });
    const setState = action => {
      hook.queue.push(action);
      this._scheduleUpdate(node);
    };
    node.states[node.stId] = hook;
    node.stId++;
    return [hook.state, setState];
  }
  /** @private */
  _runEffects() {
    let nextNode = this._root;
    while (nextNode) {
      if (nextNode.effects) {
        nextNode.effects.forEach(effect => {
          if (effect.hasChangedDeps) {
            if (effect.cleanup && effect.cleanup instanceof Function) {
              effect.cleanup();
            }
            effect.cleanup = effect.callback() || null;
          }
        });
      }
      nextNode = this._getNextNode(nextNode);
    }
  }
  useEffect(callback, deps) {
    const node = this._currentNode;
    const effectIdx = node.stId;
    const oldEffect = node.old && node.effects[effectIdx];
    const hasChangedDeps = oldEffect && oldEffect.deps ? deps.every((dep, i) => !Object.is(dep, oldEffect.deps[i])) : true;
    const effect = {
      cleanup: null,
      deps,
      callback,
      hasChangedDeps
    };

    if (hasChangedDeps) {
      if (oldEffect && oldEffect.cleanup && oldEffect.cleanup instanceof Function) {
        oldEffect.cleanup();
      }
      //const effect = async () => {
      //  let isActive = true; // Flag to track if the effect is still valid
      //  const cleanup = callback(); // Execute the user-provided effect
      //  // Check if the effect returns a cleanup function directly or from an async operation
      //  if (cleanup instanceof Promise) {
      //      cleanup.then(asyncCleanup => {
      //          if (!isActive && asyncCleanup) {
      //              asyncCleanup(); // Call the cleanup function if the component unmounted
      //          }
      //      });
      //  } else if (typeof cleanup === 'function') {
      //      node.effects[effectIdx] = { cleanup, deps }; // Store the cleanup function for later
      //  }
      //  // Define a cleanup function to update the flag if the component unmounts
      //  return () => {
      //      isActive = false;
      //  };
      //};
      node.effects[effectIdx] = effect;
    }
    node.stId++;
  }
  /**
   * 
   * @param {string | Function} type 
   * @param {object} props 
   * @param  {...FiberNode | string} children
   * @returns {FiberNode}
   */
  createElement(type, props, ...children) {
    return type
      ? new FiberNode(type, {
          ...props,
          children: children
            .flat()
            .filter(child => child)
            .map((child, idx) =>
              typeof child === "object"
                ? child.setKey(idx)
                : new FiberNode("TEXT_ELEMENT", {
                    nodeValue: child
                  }).setKey(idx))
        })
      : null;
  }

  /**
   * 
   * @param {FiberNode} element
   * @param {HTMLElement} container 
   */
  render(element, container) {
    //console.log("FTReact.render ", element);
    this._root.dom = container;
    this._root.children = [element];
    this._root.parentsSiblings();
    this._scheduleUpdate(this._root);
    //this._nextTask = this._root;
    requestIdleCallback(this._renderLoop);
  }
}
const ftReact = new FTReact();
export default ftReact;
