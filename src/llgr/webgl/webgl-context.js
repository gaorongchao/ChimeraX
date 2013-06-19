/*
 * Copyright (c) 2013 The Regents of the University of California.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms are permitted
 * provided that the above copyright notice and this paragraph are
 * duplicated in all such forms and that any documentation,
 * advertising materials, and other materials related to such
 * distribution and use acknowledge that the software was developed
 * by the University of California, San Francisco.  The name of the
 * University may not be used to endorse or promote products derived
 * from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR
 * IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
 */

var ContextInfo;

(function () {
"use strict";

ContextInfo = function (canvas, gl, render, url)
{
	this.canvas = canvas;
	this.gl = gl;
	this.render = render;
	this.url = url;
	this.requestId = null;

	var ci = this;	// for nested functions

	canvas.addEventListener("webglcontextlost",
			function (event) {
				event.preventDefault();
				var id = ci.requestId;
				ci.requestId = null;
				cancelRequestAnimFrame(id);
			},
			false);
	canvas.addEventListener("webglcontextrestored",
			function (event) {
				ci.init();
			},
			false);

	this.redraw = function () {
		if (this.render === undefined || this.requestId !== null)
			return;
		var render = this.render;
		var ci = this;
		this.requestId = requestAnimFrame(function () { render(ci); });
	};

	this.init = function () {
		llgr.set_context(this.gl);
		if (this.url == undefined) {
			llgr.clear_all();
			this.redraw();
			return;
		}

		function handler() {
			if (this.readyState != this.DONE) {
				return;
			}
			if (this.status == 200 && this.responseText != null) {
				// success!
				llgr.load_json(JSON.parse(this.responseText));
				ci.redraw();
				return;
			}
			// something went wrong
		}

		var client = new XMLHttpRequest();
		client.overrideMimeType("application/json");
		client.onreadystatechange = handler;
		client.open("GET", ci.url);
		client.send();
	};
}

}());
