 /**
 * $Id: editor_plugin_src.js 42 2006-08-08 14:32:24Z spocke $
 *
 * @author Moxiecode - based on work by Andrew Tetlaw
 * @copyright Copyright � 2004-2007, Moxiecode Systems AB, All rights reserved.
 */

function preinit() {
	// Initialize
	tinyMCE.setWindowArg('mce_windowresize', false);
}

function init() {
	tinyMCEPopup.resizeToInnerSize();
	SXE.initElementDialog('glosario');
	if (SXE.currentAction == "update") {
		SXE.showRemoveButton();
	}
}

function insertGlosario() {
	SXE.insertElement('glosario');
	tinyMCEPopup.close();	
}

function removeGlosario() {
	SXE.removeElement('glosario');
	tinyMCEPopup.close();
}