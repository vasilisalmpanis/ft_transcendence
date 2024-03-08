const isEvent = key => key.startsWith("on");
const isProperty = key => key !== "children" && !isEvent(key);
const isNew = (prev, next) => key => prev[key] !== next[key];
const isGone = (prev, next) => key => !(key in next);

//let currentNode = null;
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
		this.needsUpdate = true;
		this.states = [];
		this.stId = 0;
	}

	get child() {
		return (
			this.props.children
			&& this.props.children[0]
		) || null;
	}

	set child(val) {
		this.props.children[0] = val;
	}

	get children() {
		return (
			this.props
			&& this.props.children
		) || null;
	}

	set children(val) {
		if (!this.props)
			this.props = {};
		this.props.children = val;
	}

	get sibling() {
		return (
			this.parent
			&& this.parent.children
			&& this.parent.children[this.key + 1]
		) || null;
	}

	set sibling(val) {
		if (this.parent) {
			val.key = this.key + 1;
			this.parent.children[this.key + 1] = val;
		}
	}

	setKey(key) {
		this.key = key;
		return this;
	}

	parentsSiblings() {
		if (!this.props || !this.props.children)
			return;
		this.props.children.forEach((child, idx) => {
			child.parent = this;
			child.key = idx;
			child.parentsSiblings();
		});
	}

	resolveFunc(ftReact) {
		this.stId = 0;
		ftReact._currentNode = this;
		const children = this.type(this.props);
		ftReact._currentNode = null;
		this.props.children = Array.isArray(children) ? children : [children];
		this.parentsSiblings();
	}

	clone() {
		const clonedProps = {
			...this.props,
			children: this.props.children.map(
				child => child instanceof FiberNode
					? child.clone()
					: child
			)
		};
		const clonedNode = new FiberNode(this.type, clonedProps);
		clonedNode.dom = this.dom;
		clonedNode.needsUpdate = this.needsUpdate;
		clonedNode.states = [...this.states];
		clonedNode.key = this.key;
		clonedNode.parent = this.parent;
		return clonedNode;
	}

	/**
	 * @param {FiberNode[]} children
	 */
	reconcile(children, deletions) {
		//console.log("  VNode.reconcile RECONCILE: ", this, children);
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
				deletions.push(oldNode);
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
	}

	commit() {
		//console.log("  VNode.commit ", this);
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
		this.child && this.child.commit();
		this.sibling && this.sibling.commit();
		this.old = this.clone();
	}

	delete(domParent) {
		console.log("  VNode.delete", this);
		if (this.dom)
			domParent.removeChild(this.dom);
		else
			this.child && this.child.delete(domParent);
	}

	update(ftReact) {
		//console.log("  VNode.update", this);
		if (this.type instanceof Function)
			this.resolveFunc(ftReact);
		else if (!this.dom)
			this.createDom();
		this.reconcile(this.props.children, ftReact.deletions);
	}

	createDom() {
		//console.log("  VNode.createDom", this);
		this.dom = this.type == "TEXT_ELEMENT"
			? document.createTextNode("")
			: document.createElement(this.type);
		this.updateDom();

	}

	updateDom = () => {
		console.log("  VNode.updateDom", this);
		const oldProps = (this.old && this.old.props) || {};
		//Remove old or changed event listeners
		Object.keys(oldProps)
			.filter(isEvent)
			.filter(
				key =>
					!(key in this.props) ||
					isNew(oldProps, this.props)(key)
			)
			.forEach(name => {
				const eventType = name
					.toLowerCase()
					.substring(2);
				this.dom.removeEventListener(
					eventType,
					oldProps[name]
				);
			});

		// Remove old properties
		Object.keys(oldProps)
			.filter(isProperty)
			.filter(isGone(oldProps, this.props))
			.forEach(name => {
				this.dom[name] = "";
			});

		// Set new or changed properties
		Object.keys(this.props)
			.filter(isProperty)
			.filter(isNew(oldProps, this.props))
			.forEach(name => {
				this.dom[name] = this.props[name];
			});

		// Add event listeners
		Object.keys(this.props)
			.filter(isEvent)
			.filter(isNew(oldProps, this.props))
			.forEach(name => {
				const eventType = name
					.toLowerCase()
					.substring(2);
				this.dom.addEventListener(
					eventType,
					this.props[name]
				);
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
	}

	/** @private */
	_change() {
		//console.log("FTReact.change NEXT TASK: ", this._nextTask);
		this._nextTask.update(this);
		this._newChanges = true;
		if (this._nextTask.child) {
			this._nextTask = this._nextTask.child;
			return;
		}
		let nextNode = this._nextTask;
		while (nextNode) {
			if (nextNode.sibling) {
				this._nextTask = nextNode.sibling;
				return;
			}
			nextNode = nextNode.parent;
		}
		this._nextTask = null;
	}

	/** @private */
	_commit() {
		console.log("FTReact.commit");
		this._deletions.forEach(el => el.commit());
		this._root.child && this._root.child.commit();
		this._newChanges = false;
	}

	/** @private */
	_renderLoop(deadline) {
		let shouldYield = false;
		while (this._nextTask && !shouldYield) {
			this._change();
			shouldYield = deadline.timeRemaining() < 1;
		}
		if (!this._nextTask && this._newChanges) {
			this._commit();
		}
		requestIdleCallback(this._renderLoop);
	}

	_resolveFuncComponents() {
		this._root.parentsSiblings();
		let nextNode = this._root;
		while (nextNode) {
			if (nextNode.child)
				nextNode = nextNode.child;
			else if (nextNode.sibling)
				nextNode = nextNode.sibling;
			else {
				let parentNode = nextNode.parent;
				if (!parentNode)
					return;
				nextNode = parentNode.sibling;
				while (!nextNode) {
					parentNode = parentNode.parent;
					if (!parentNode)
						return;
					nextNode = parentNode.sibling;
				}
			}
			if (nextNode.type instanceof Function)
				nextNode.resolveFunc();
		}
	}

	useState(initialValue) {
		const node = this._currentNode;
		const oldHook = node.old && node.old.states[node.stId];
		const hook = {
			state: oldHook ? oldHook.state : initialValue,
			queue: [],
		};
		const actions = oldHook ? oldHook.queue : [];
		actions.forEach(action => {
			hook.state = action instanceof Function ? action(hook.state) : action;
		});
		const setState = (action) => {
			hook.queue.push(action);
			this._nextTask = node;
			console.log(this._nextTask);
		};
		node.states[node.stId] = hook;
		node.stId++;
		return [hook.state, setState];
	}

	/**
	 * 
	 * @param {string | Function} type 
	 * @param {object} props 
	 * @param  {...FiberNode | string} children
	 * @returns {FiberNode}
	 */
	createElement(type, props, ...children) {
		return new FiberNode(
			type,
			{
				...props,
				children: children.map(
					(child, idx) => typeof child === "object"
						? child.setKey(idx)
						: new FiberNode(
							"TEXT_ELEMENT",
							{ nodeValue: child }
						).setKey(idx)
				)
			},
		);
	}

	/**
	 * 
	 * @param {FiberNode} element
	 * @param {HTMLElement} container 
	 */
	render(element, container) {
		console.log("FTReact.render ", element);
		this._root.dom = container;
		this._root.props.children = [element];
		this._root.parentsSiblings();
		this._nextTask = this._root;
		requestIdleCallback(this._renderLoop);
	}
}

const ftReact = new FTReact();
export default ftReact;
