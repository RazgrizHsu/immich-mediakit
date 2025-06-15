window.dash_clientside = window.dash_clientside || {}

const R = {
    mk(t, props, ...children) {
        return React.createElement(t, props, ...children)
    }
}

function notify(msg, type = 'info') {

    const el = document.createElement('div');

    el.textContent = msg;
    el.style.position = 'fixed';
    el.style.top = '70%';
    el.style.left = '50%';
    el.style.transform = 'translate(-50%, -50%)';
    el.style.padding = '10px 15px';
    el.style.zIndex = 9999;
    //el.style.background = type == 'info' ? '#4CAF50' : '#F44336';

	el.style.background = `linear-gradient(to bottom, ${ type == 'info' ? '#4CAF50, #00C853' : '#F44336, #D50000' })`
    el.style.color = 'white';
    el.style.borderRadius = '4px';
    el.style.boxShadow = '0 2px 5px rgba(0,0,0,0.3)';
    el.style.opacity = 0;
    el.style.transition = 'opacity 0.3s';

    document.body.appendChild(el);

    setTimeout(() => { el.style.opacity = 1 }, 10);
    setTimeout(() => {
        el.style.opacity = 0;
        el.addEventListener('transitionend', function handler() {
            el.remove();
            el.removeEventListener('transitionend', handler); // Clean up the event listener
        });
    }, 2000);
}


const dsh = {

	syncStore( key, data ){

		if ( !window.dash_clientside || !window.dash_clientside.set_props )
			console.error( `[mdlImg] error not found dash client side...` )

		let str = `data( ${typeof data} )`
		const entries = Object.entries( data ).map( ( [k, v] ) => `${k}: (${typeof v})[${v}]` ).join( ', ' )
		str += ` entries: {${entries}}`

		console.info( `[dsh] sync store[ ${key} ] ${str}` )
		window.dash_clientside.set_props( key, {data} )
	},

	syncSte( cnt, selectedIds ){

		if ( !Array.isArray( selectedIds ) ) selectedIds = Array.from( selectedIds )

		this.syncStore( 'store-state', {cntTotal: cnt, selectedIds: selectedIds} )
	}

}




function getCardById(targetId) {
	const cards = document.querySelectorAll(`[id*='"type":"card-select"']`);
	// console.log(`[getCardById] Looking for targetId: ${targetId} (type: ${typeof targetId}), found ${cards.length} cards`);

	for (const cd of cards) {
		try {
			const idAttr = JSON.parse(cd.id);
			const cardId = parseInt(idAttr.id)
			const searchId = parseInt(targetId)

			// console.log(`[getCardById] Checking card: cardId=${cardId} (type: ${typeof cardId}), searchId=${searchId} (type: ${typeof searchId}), type=${idAttr.type}`);
			if (cardId == searchId && idAttr.type == "card-select") {
				// console.log(`[getCardById] Found matching card for ID: ${targetId}`);
				return cd
			}
		} catch (e) {
			console.error("Error parsing ID attribute:", cd.id, e);
		}
	}
	console.warn(`[getCardById] No card found for targetId: ${targetId}`);
	return null; // Card not found
}

const Ste = window.Ste = {
	cntTotal: 0,
	selectedIds: new Set(),
	_lastSyncHash: null,

	init( cnt ){
		this.cntTotal = cnt
		this.selectedIds.clear()
		console.log( `[Ste] Initialized with ${cnt} assets, selected[ ${this.selectedIds.size} ]` )

		dsh.syncSte( this.cntTotal, this.selectedIds )
	},

	initSilent( cnt ){
		this.cntTotal = cnt
		this.selectedIds.clear()
		console.log( `[Ste] Silent init with ${cnt} assets, selected[ ${this.selectedIds.size} ]` )
	},

	toggle( aid ){
		this.selectedIds.has(aid) ? this.selectedIds.delete(aid) : this.selectedIds.add(aid);

		console.log( `[Ste] Toggled ${aid}, selected count: ${this.selectedIds.size}` )

		this.updCss( aid )
		this.updBtns()
	},

	updCss( aid ){
		// console.log( `[Ste] updCss called for aid: ${aid} (type: ${typeof aid})` )

		let card = getCardById(aid)
		if ( !card ){
			console.error( `[Ste] No cards found for ${aid}` )

			const allCards = document.querySelectorAll(`[id*='"type":"card-select"']`);
			console.log( `[Ste] Available cards:` )
			allCards.forEach( (c, idx) => {
				try {
					const idAttr = JSON.parse(c.id);
					console.log( `[Ste] Card[${idx}] id[${idAttr.id}] (type: ${typeof idAttr.id}), type=${idAttr.type}` )
				} catch (e) {
					console.log( `[Ste] Card ${idx}: parse error for ${c.id}` )
				}
			})
			return
		}

		const par = card.closest( '.card' )
		const cbx = card.querySelector( 'input[type="checkbox"]' )
		const isSelected = this.selectedIds.has( aid )

		// console.log( `[Ste] updCss ${aid}: isSelected[${isSelected}], parentCard[${!!par}], checkbox[${!!cbx}]` )

		if( !par ) console.error( `[updCss] not found aid[${aid}] card` )

		if ( par ) {
			par.classList[ isSelected ? 'add' : 'remove' ]( 'checked' )
			// console.log( `[Ste:updCss] Updated card ${aid} visual state: ${isSelected ? 'checked' : 'unchecked'}` )
		}

		if ( cbx ) cbx.checked = isSelected
	},

	updBtns(){
		const cntSel = this.selectedIds.size
		const cntAll = this.cntTotal
		const cntDiff = cntAll - cntSel

		const btnRm = document.getElementById( 'sim-btn-RmSel' )
		const btnRS = document.getElementById( 'sim-btn-OkSel' )
		const btnAllSelect = document.getElementById( 'sim-btn-AllSelect' )
		const btnAllCancel = document.getElementById( 'sim-btn-AllCancel' )

		if ( btnRm ) btnRm.textContent = `❌ Delete( ${cntSel} ) and ✅ Keep others( ${cntDiff} )`
		if ( btnRS ) btnRS.textContent = `✅ Keep( ${cntSel} ) and ❌ delete others( ${cntDiff} )`

		if ( btnAllSelect ) btnAllSelect.disabled = ( cntSel >= cntAll || cntAll == 0 )
		if ( btnAllCancel ) btnAllCancel.disabled = ( cntSel == 0 )

		console.log( `[Ste] updBtns - selected[ ${cntSel} / ${cntAll} ]` )
	},

	selectAll(){
		const cards = document.querySelectorAll( '[id*="card-select"]' )
		cards.forEach( card => {
			const assetId = this.extractAssetIdBy( card )
			if ( assetId ) this.selectedIds.add( assetId )
		} )
		this.updAllCss()
		this.updBtns()
		console.log( `[Ste] Selected all ${this.selectedIds.size} assets` )
		dsh.syncSte( this.cntTotal, this.selectedIds )
	},

	clearAll(){
		this.selectedIds.clear()
		this.updAllCss()
		this.updBtns()
		console.log( `[Ste] Cleared all selections` )
		dsh.syncSte( this.cntTotal, this.selectedIds )
	},

	updAllCss(){
		const cards = document.querySelectorAll( '[id*="card-select"]' )
		console.log( `[Ste] updAllCss cards[ ${cards.length} ]` )
		cards.forEach( card => {
			const assetId = this.extractAssetIdBy( card )
			if ( assetId ) this.updCss( assetId )
		} )
	},

	extractAssetIdBy( elem ){
		try{
			const idStr = elem.getAttribute( 'id' )
			if ( idStr && idStr.includes( 'card-select' ) )
			{
				const match = idStr.match( /"id":(\d+)/ )
				return match ? parseInt(match[1]) : null // Return number instead of string
			}
		}
		catch ( e ) { console.error( '[Ste] Error extracting asset ID:', e ) }
		return null
	},

	getGroupCards( groupId ){
		const cards = []
		const gv = document.querySelector( '.gv' )

		if ( !gv ){
			console.warn( `[Ste] No .gv container found` )
			return cards
		}

		const chs = Array.from( gv.children )
		let collecting = false

		chs.forEach( child => {
			if ( child.classList.contains( 'hr' ) ){
				const label = child.querySelector( 'label' )
				if ( label ){
					const match = label.textContent.match( /Group (\d+)/ )
					if ( match ){
						let gid = parseInt( match[1] )
						collecting = ( gid == groupId )
					}
				}
			} else if ( collecting ){
				const cardSelect = child.querySelector( '[id*="card-select"]' )
				if ( cardSelect ){
					cards.push( cardSelect )
				} else {
					collecting = false
				}
			}
		} )

		console.log( `[Ste] Found ${cards.length} cards for group ${groupId}` )
		return cards
	},

	selectGroup( groupId ){
		const grps = this.getGroupCards( groupId )
		let cnt = 0

		grps.forEach( card => {
			const assetId = this.extractAssetIdBy( card )
			if ( assetId && !this.selectedIds.has( assetId ) ){
				this.selectedIds.add( assetId )
				this.updCss( assetId )
				cnt++
			}
		} )

		this.updBtns()
		console.log( `[Ste] Selected ${cnt} items in group ${groupId}` )
		dsh.syncSte( this.cntTotal, this.selectedIds )
	},

	clearGroup( groupId ){
		const cards = this.getGroupCards( groupId )
		let deselectedCount = 0

		cards.forEach( card => {
			const assetId = this.extractAssetIdBy( card )
			if ( assetId && this.selectedIds.has( assetId ) ){
				this.selectedIds.delete( assetId )
				this.updCss( assetId )
				deselectedCount++
			}
		} )

		this.updBtns()
		console.log( `[Ste] Deselected ${deselectedCount} items in group ${groupId}` )
		dsh.syncSte( this.cntTotal, this.selectedIds )
	},
}


//------------------------------------------------------------------------
// mdlImg Client State Manager
//------------------------------------------------------------------------
const MdlImg = window.MdlImg = {
	state: {
		mdl: null,
		now: null,
		ste: null
	},

	init( mdlData, nowData, steData ){
		this.state.mdl = mdlData
		this.state.now = nowData
		this.state.ste = steData

		console.info( `[mdlImg] init ste, cntTotal[ ${steData.cntTotal} ] selected( ${steData.selectedIds.length} )[ ${steData.selectedIds} ]` )
		return this
	},

	navigate( direction ){
		if ( !this.state.mdl || !this.state.mdl.isMulti || !this.state.now?.sim?.assCur )
			return this.noUpdate( 6 )

		const assets = this.state.now.sim.assCur
		let newIdx = this.state.mdl.curIdx

		if ( direction == 'prev' && newIdx > 0 ) newIdx = newIdx - 1
		else if ( direction == 'next' && newIdx < assets.length - 1 ) newIdx = newIdx + 1
		else return this.noUpdate( 6 )

		const curAss = assets[ newIdx ]
		const newMdl = {
			...this.state.mdl,
			curIdx: newIdx,
			imgUrl: `/api/img/${curAss.autoId}?q=preview`
		}

		const htms = this.buildImageContent( newMdl )
		const prevStyle = this.getPrevButtonStyle( newMdl )
		const nextStyle = this.getNextButtonStyle( newMdl )
		const selectText = this.getSelectButtonText( newMdl, curAss )
		const selectColor = this.getSelectButtonColor( newMdl, curAss )

		console.log( `[MdlImg] navigated to idx[${newIdx}] autoId[${curAss.autoId}]` )

		return [newMdl, htms, prevStyle, nextStyle, selectText, selectColor]
	},

	buildImageContent( mdl ){
		const htms = []

		if ( mdl.isMulti && this.state.now?.sim?.assCur && mdl.curIdx < this.state.now.sim.assCur.length ){
			const ass = this.state.now.sim.assCur[ mdl.curIdx ]

			if ( ass && ass.vdoId ){
				htms.push(
					R.mk( 'div', {className: 'livephoto'},
						R.mk( 'video', {
							src: `/api/livephoto/${ass.autoId}`,
							id: `livephoto-modal-video-${ass.autoId}`,
							autoPlay: true,
							loop: true,
							muted: true,
							controls: false
						}),
						R.mk( 'div', {className: 'ctrls', id: 'livephoto-controls'},
							R.mk( 'button', {className: 'play-pause-btn', id: 'livephoto-play-pause'}, '⏸️' ),
							R.mk( 'div', {className: 'progress-bar', id: 'livephoto-progress-bar'},
								R.mk( 'div', {className: 'progress-fill', id: 'livephoto-progress-fill'} )
							),
							R.mk( 'div', {className: 'time-display', id: 'livephoto-time-display'}, '0:00 / 0:00' )
						)
					)
				)
			}
			else if ( mdl.imgUrl ) htms.push( R.mk( 'img', {src: mdl.imgUrl} ) )

			if ( ass ){
				htms.push(
					R.mk( 'div', {className: 'acts B'},
						R.mk( 'span', {className: 'tag xl'},
							`#${ass.autoId} @${ass.simGIDs?.join( ',' ) || ''}`
						)
					)
				)
			}
		}
		else if ( mdl.imgUrl ) htms.push( R.mk( 'img', {src: mdl.imgUrl} ) )

		return htms
	},

	getPrevButtonStyle( mdl ){
		if ( !mdl.isMulti || !this.state.now?.sim?.assCur || this.state.now.sim.assCur.length <= 1 ) return {display: 'none'}

		return {
			display: 'block',
			opacity: mdl.curIdx <= 0 ? '0.3' : '1'
		}
	},

	getNextButtonStyle( mdl ){
		if ( !mdl.isMulti || !this.state.now?.sim?.assCur || this.state.now.sim.assCur.length <= 1 ) return {display: 'none'}

		return {
			display: 'block',
			opacity: mdl.curIdx >= this.state.now.sim.assCur.length - 1 ? '0.3' : '1'
		}
	},

	getSelectButtonText( mdl, curAss ){
		if ( !mdl.isMulti || !curAss ) return '◻️ Select'

		const isSelected = this.state.ste?.selectedIds?.includes( curAss.autoId )
		return isSelected ? '✅ Selected' : '◻️ Select'
	},

	getSelectButtonColor( mdl, curAss ){
		if ( !mdl.isMulti || !curAss ) return 'primary'

		const isSelected = this.state.ste?.selectedIds?.includes( curAss.autoId )
		return isSelected ? 'success' : 'primary'
	},

	noUpdate( cnt ){
		return Array( cnt ).fill( dash_clientside.no_update )
	},

	updateModalContent(){
		if ( !this.state.mdl || !this.state.mdl.open ) return this.noUpdate( 12 )

		const mdl = this.state.mdl
		const htms = this.buildImageContent( mdl )
		const prevStyle = this.getPrevButtonStyle( mdl )
		const nextStyle = this.getNextButtonStyle( mdl )
		const selectStyle = this.getSelectButtonStyle( mdl )
		const selectText = this.getSelectButtonText( mdl, this.getCurrentAsset() )
		const selectColor = this.getSelectButtonColor( mdl, this.getCurrentAsset() )
		const helpCss = this.getHelpClassName( mdl )
		const helpTxt = this.getHelpButtonText( mdl )
		const infoCss = this.getInfoClassName( mdl )
		const infoTxt = this.getInfoButtonText( mdl )
		const infoContent = this.getInfoContent( mdl )

		return [
			mdl.open,
			htms,
			prevStyle,
			nextStyle,
			selectStyle,
			selectText,
			selectColor,
			helpCss,
			helpTxt,
			infoCss,
			infoTxt,
			infoContent
		]
	},

	getCurrentAsset(){
		if ( !this.state.mdl?.isMulti || !this.state.now?.sim?.assCur ) return null

		const idx = this.state.mdl.curIdx
		const assets = this.state.now.sim.assCur
		return ( idx >= 0 && idx < assets.length ) ? assets[ idx ] : null
	},

	getSelectButtonStyle( mdl ){
		return mdl.isMulti ? {display: 'block'} : {display: 'none'}
	},

	getHelpClassName( mdl ){
		if ( !mdl.isMulti ) return 'hide'
		return mdl.helpCollapsed ? 'help collapsed' : 'help'
	},

	getHelpButtonText( mdl ){
		return mdl.helpCollapsed ? '❔' : '❎'
	},

	getInfoClassName( mdl ){
		if ( !mdl.isMulti ) return 'hide'
		return mdl.infoCollapsed ? 'info collapsed' : 'info'
	},

	getInfoButtonText( mdl ){
		return mdl.infoCollapsed ? 'ℹ️' : '❎'
	},

	getInfoContent( mdl ){
		if ( !mdl.isMulti || !this.state.now?.sim?.assCur ) return []

		const ass = this.getCurrentAsset()
		if ( !ass ) return []

		const assetRows = [
			R.mk( 'tr', {},
				R.mk( 'td', {}, 'autoId' ),
				R.mk( 'td', {},
					R.mk( 'span', {className: 'tag'}, `#${ass.autoId}` ),
					R.mk( 'span', {className: 'tag'}, `@${ass.simGIDs?.join( ',' ) || ''}` )
				)
			),
			R.mk( 'tr', {},
				R.mk( 'td', {}, 'id' ),
				R.mk( 'td', {}, R.mk( 'span', {className: 'tag sm second'}, ass.id ) )
			),
			R.mk( 'tr', {},
				R.mk( 'td', {}, 'Filename' ),
				R.mk( 'td', {}, ass.originalFileName )
			)
		]

		const exifRows = this.buildExifRows( ass )
		const allRows = [...assetRows, ...exifRows]

		return R.mk( 'table', {className: 'table-sm table-striped', style: {width: '100%'}},
			R.mk( 'tbody', {}, ...allRows )
		)
	},

	buildExifRows( asset ){
		const rows = []

		if ( !asset.jsonExif ) return rows

		const exifMap = {
			"exifImageWidth": "Width",
			"exifImageHeight": "Height",
			"fileSizeInByte": "File Size",
			"dateTimeOriginal": "Capture Time",
			"modifyDate": "Modify Time",
			"make": "Camera Brand",
			"model": "Camera Model",
			"lensModel": "Lens",
			"fNumber": "Aperture",
			"focalLength": "Focal Length",
			"exposureTime": "Exposure Time",
			"iso": "ISO",
			"orientation": "Orientation",
			"latitude": "Latitude",
			"longitude": "Longitude",
			"city": "City",
			"state": "State",
			"country": "Country",
			"description": "Description",
			"fps": "Frame Rate"
		}

		for ( const [key, displayKey] of Object.entries( exifMap ) ){
			if ( key in asset.jsonExif && asset.jsonExif[ key ] != null ){
				let value = asset.jsonExif[ key ]
				let displayValue = value

				if ( key == "fileSizeInByte" ) displayValue = this.formatFileSize( value )
				else if ( key == "focalLength" && typeof value == 'number' ) displayValue = `${value} mm`
				else if ( key == "fNumber" && typeof value == 'number' ) displayValue = `f/${value}`
				else if ( value ) displayValue = this.formatDate( value )

				if ( displayValue ){
					rows.push(
						R.mk( 'tr', {},
							R.mk( 'td', {}, displayKey ),
							R.mk( 'td', {}, displayValue )
						)
					)
				}
			}
		}

		return rows
	},

	formatFileSize( value ){
		if ( typeof value == 'number' ){
			if ( value > 1024 * 1024 ){
				return `${( value / ( 1024 * 1024 ) ).toFixed( 2 )} MB`
			}
			else if ( value > 1024 ){
				return `${( value / 1024 ).toFixed( 2 )} KB`
			}
			else{
				return `${value} B`
			}
		}
		return value
	},

	formatDate( value ){
		const str = String( value )
		if ( str.includes( 'T' ) && str.includes( '+' ) ){
			const parts = str.split( 'T' )
			if ( parts.length == 2 && parts[ 1 ].includes( '+' ) ){
				const timePart = parts[ 1 ]
				if ( timePart.includes( '.' ) && ( timePart.includes( '+' ) || timePart.includes( '-' ) ) ){
					const timeParts = timePart.split( '.' )
					if ( timeParts.length == 2 ){
						const baseTime = timeParts[ 0 ]
						const tzPart = timeParts[ 1 ].includes( '+' ) ?
							timeParts[ 1 ].split( '+' )[ 1 ] : timeParts[ 1 ].split( '-' )[ 1 ]
						const sign = timeParts[ 1 ].includes( '+' ) ? '+' : '-'
						const tz = `${baseTime}${sign}${tzPart}`
						return `${parts[ 0 ]} ${tz}`
					}
				}
			}
		}
		return str
	},

	toggleHelp(){
		if ( !this.state.mdl ) return this.noUpdate( 3 )

		const newMdl = {
			...this.state.mdl,
			helpCollapsed: !this.state.mdl.helpCollapsed
		}

		const helpCss = this.getHelpClassName( newMdl )
		const helpTxt = this.getHelpButtonText( newMdl )

		return [newMdl, helpCss, helpTxt]
	},

	toggleInfo(){
		if ( !this.state.mdl ) return this.noUpdate( 3 )

		const newMdl = {
			...this.state.mdl,
			infoCollapsed: !this.state.mdl.infoCollapsed
		}

		const infoCss = this.getInfoClassName( newMdl )
		const infoTxt = this.getInfoButtonText( newMdl )

		return [newMdl, infoCss, infoTxt]
	},

	toggleMode( currentClasses ){
		if ( !currentClasses ) currentClasses = ""

		const hasAuto = currentClasses.split( ' ' ).includes( 'auto' )

		let newCss, newTxt
		if ( hasAuto ){
			newCss = currentClasses.split( ' ' ).filter( c => c != 'auto' ).join( ' ' )
			newTxt = '🔄 Fixed Height'
		}
		else{
			newCss = currentClasses ? `${currentClasses} auto` : 'auto'
			newTxt = '🔄 Auto Height'
		}

		return [newCss, newTxt]
	}
}

//------------------------------------------------------------------------
// LivePhoto Management
//------------------------------------------------------------------------
const LivePhoto = window.LivePhoto = {
	hoveredVideo: null,
	modalVideo: null,

	init() {
		this.setupHover()
		this.setupModalControls()
	},

	setupHover() {
		document.addEventListener('mouseenter', (e) => {
			const card = e.target.closest('.card')
			if (!card) return

			const livePhotoOverlay = card.querySelector('.livephoto-overlay')
			if (!livePhotoOverlay || livePhotoOverlay.style.display == 'none') return

			const video = livePhotoOverlay.querySelector('.livephoto-video')
			if (video) {
				this.hoveredVideo = video
				video.style.display = 'block'
				video.play().catch(e => console.warn('Video play failed:', e))
			}
		}, true)

		document.addEventListener('mouseleave', (e) => {
			const card = e.target.closest('.card')
			if (!card) return

			if (this.hoveredVideo) {
				this.hoveredVideo.pause()
				this.hoveredVideo.currentTime = 0
				this.hoveredVideo.style.display = 'none'
				this.hoveredVideo = null
			}
		}, true)
	},

	setupModalControls() {
		document.addEventListener('click', (e) => {
			if (e.target.id == 'livephoto-play-pause') {
				this.toggleModalPlayback()
			} else if (e.target.id == 'livephoto-progress-bar' || e.target.parentElement.id == 'livephoto-progress-bar') {
				this.seekModalVideo(e)
			}
		})

		setInterval(() => { this.updateModalProgress() }, 100)
	},

	toggleModalPlayback() {
		const video = document.querySelector('.livephoto video')
		const button = document.getElementById('livephoto-play-pause')

		if (!video || !button) return

		if (video.paused) {
			video.play()
			button.textContent = '⏸️'
		} else {
			video.pause()
			button.textContent = '▶️'
		}
	},

	seekModalVideo(e) {
		const video = document.querySelector('.livephoto video')
		const progressBar = document.getElementById('livephoto-progress-bar')

		if (!video || !progressBar) return

		const rect = progressBar.getBoundingClientRect()
		const clickX = e.clientX - rect.left
		const percentage = clickX / rect.width
		const seekTime = percentage * video.duration

		video.currentTime = seekTime
	},

	updateModalProgress() {
		const video = document.querySelector('.livephoto video')
		const progressFill = document.getElementById('livephoto-progress-fill')
		const timeDisplay = document.getElementById('livephoto-time-display')

		if (!video || !progressFill || !timeDisplay) return

		if (video.duration > 0) {
			const percentage = (video.currentTime / video.duration) * 100
			progressFill.style.width = percentage + '%'

			const currentMin = Math.floor(video.currentTime / 60)
			const currentSec = Math.floor(video.currentTime % 60)
			const totalMin = Math.floor(video.duration / 60)
			const totalSec = Math.floor(video.duration % 60)

			timeDisplay.textContent = `${currentMin}:${currentSec.toString().padStart(2, '0')} / ${totalMin}:${totalSec.toString().padStart(2, '0')}`
		}
	}
}

if (document.readyState == 'loading') {
	document.addEventListener('DOMContentLoaded', () => LivePhoto.init())
} else {
	LivePhoto.init()
}




//------------------------------------------------------------------------
// similar
//------------------------------------------------------------------------
window.dash_clientside.similar = {

	onCardSelectClicked( n_clicks ){
		if ( dash_clientside.callback_context.triggered.length > 0 ){
			let triggered = dash_clientside.callback_context.triggered[ 0 ]
			if ( triggered.prop_id && triggered.value > 0 ){
				let triggeredId = JSON.parse( triggered.prop_id.split( '.' )[ 0 ] )
				Ste.toggle( triggeredId.id )

				let steData = {
					cntTotal: Ste.cntTotal,
					selectedIds: Array.from( Ste.selectedIds ),
				}

				console.log( '[Ste] Syncing to ste store on selection:', steData )
				return steData
			}
		}
		return dash_clientside.no_update
	},

	onNowSyncToDummyInit( now_data, ste_data ){
		if ( now_data && now_data.sim && now_data.sim.assCur ){
			let assets = now_data.sim.assCur
			if ( Ste ){
				const selectedIdsArray = ste_data && ste_data.selectedIds ? ste_data.selectedIds : []
				const syncHash = `${assets.length}-${selectedIdsArray.join(',')}`

				if ( Ste._lastSyncHash == syncHash ){
					console.log( `[Ste] Skipping duplicate sync for hash: ${syncHash}` )
					return dash_clientside.no_update
				}

				Ste._lastSyncHash = syncHash

				// Initialize without triggering sync (silent mode)
				Ste.initSilent( assets.length )

				// Sync initial selection from ste store without triggering events
				if ( ste_data && ste_data.selectedIds && Array.isArray( ste_data.selectedIds ) ){
					for ( const autoId of ste_data.selectedIds ) Ste.selectedIds.add( autoId )

					setTimeout( () => {
						const cards = document.querySelectorAll(`[id*='"type":"card-select"']`);
						if ( cards.length > 0 ){
							Ste.updAllCss()
							Ste.updBtns()
							console.log( `[Ste] Synced ${ste_data.selectedIds.length} initial selections from server:`, ste_data.selectedIds )
						} else {
							console.log( `[Ste] Cards not ready, retrying in 200ms...` )
							setTimeout( () => {
								Ste.updAllCss()
								Ste.updBtns()
								console.log( `[Ste] Retry synced ${ste_data.selectedIds.length} initial selections from server:`, ste_data.selectedIds )
							}, 200 )
						}
					}, 300 )
				} else {
					setTimeout( () => {
						Ste.updBtns()
						console.log( `[Ste] Initialized with ${assets.length} assets, no initial selections` )
					}, 300 )
				}
			}
		}
		return dash_clientside.no_update
	}
}


//------------------------------------------------------------------------
// mdlImg
//------------------------------------------------------------------------
window.dash_clientside.mdlImg = {
	onStoreToDummy( mdl_data, now_data ){
		if ( mdl_data && mdl_data.isMulti && now_data && now_data.sim && now_data.sim.assCur ){
			let curIdx = mdl_data.curIdx
			let assets = now_data.sim.assCur

			if ( curIdx >= 0 && curIdx < assets.length ){
				let curAsset = assets[ curIdx ]
				window.currentMdlImgAutoId = curAsset.autoId
				console.log( '[mdlImg] Set current autoId for hotkeys:', window.currentMdlImgAutoId )
			}
		}
		else{
			window.currentMdlImgAutoId = null
		}
		return dash_clientside.no_update
	},
	onBtnSelectToSte( n_clicks ){
		if ( dash_clientside.callback_context.triggered.length > 0 ){
			let triggered = dash_clientside.callback_context.triggered[ 0 ]
			if ( triggered.prop_id && triggered.value > 0 ){
				let mdlData = arguments[ arguments.length - 1 ] // mdlImg store data
				let nowData = arguments[ arguments.length - 2 ] // now store data

				if ( mdlData && mdlData.isMulti && nowData && nowData.sim && nowData.sim.assCur ){
					let curIdx = mdlData.curIdx
					let assets = nowData.sim.assCur

					if ( curIdx >= 0 && curIdx < assets.length ){
						let curAsset = assets[ curIdx ]
						let autoId = curAsset.autoId

						if ( Ste ){
							Ste.toggle( autoId )

							let selectedIds = Array.from( Ste.selectedIds )
							let totalCount = Ste.cntTotal

							let steData = {
								selectedIds: selectedIds,
								cntTotal: totalCount
							}

							console.log( '[mdlImg] Toggled autoId:', autoId, 'steData:', steData )
							return steData
						}
					}
				}
			}
		}
		return dash_clientside.no_update
	},

	onNavigation( prevClk, nextClk, nowData, steData, mdlData ){
		const ctx = dash_clientside.callback_context
		if ( !ctx.triggered.length ) return dash_clientside.no_update

		MdlImg.init( mdlData, nowData, steData )

		const trigId = ctx.triggered[ 0 ].prop_id
		if ( trigId.includes( 'btn-img-prev' ) ) return MdlImg.navigate( 'prev' )
		if ( trigId.includes( 'btn-img-next' ) ) return MdlImg.navigate( 'next' )

		return dash_clientside.no_update
	},

	onContentUpdate( mdlData, nowData, steData ){
		MdlImg.init( mdlData, nowData, steData )
		return MdlImg.updateModalContent()
	},

	onHelpToggle( nClicks, mdlData ){
		if ( !nClicks ) return Array( 3 ).fill( dash_clientside.no_update )

		MdlImg.init( mdlData, null, null )
		return MdlImg.toggleHelp()
	},

	onInfoToggle( nClicks, mdlData ){
		if ( !nClicks ) return Array( 3 ).fill( dash_clientside.no_update )

		MdlImg.init( mdlData, null, null )
		return MdlImg.toggleInfo()
	},

	onModeToggle( nClicks, currentClasses ){
		if ( !nClicks ) return Array( 2 ).fill( dash_clientside.no_update )

		return MdlImg.toggleMode( currentClasses )
	},

	onSteChanged( steData, nowData, mdlData ){
		if ( !steData || !nowData || !mdlData ) return Array( 2 ).fill( dash_clientside.no_update )

		MdlImg.init( mdlData, nowData, steData )

		if ( !mdlData.isMulti || !nowData.sim?.assCur || mdlData.curIdx >= nowData.sim.assCur.length ){
			return Array( 2 ).fill( dash_clientside.no_update )
		}

		const curAss = nowData.sim.assCur[ mdlData.curIdx ]
		if ( !curAss ) return Array( 2 ).fill( dash_clientside.no_update )

		const selectText = MdlImg.getSelectButtonText( mdlData, curAss )
		const selectColor = MdlImg.getSelectButtonColor( mdlData, curAss )

		console.log( `[MdlImg] Updated button state for autoId[${curAss.autoId}]` )

		return [selectText, selectColor]
	}
}

//========================================================================
// global
//========================================================================
document.addEventListener( 'keydown', function ( ev ){
	const div = document.querySelector( '#img-modal' )

	if ( !div || !div.parentElement.classList.contains( 'show' ) ) return
	if ( ev.key == 'ArrowLeft' || ev.key == 'h' )
	{
		ev.preventDefault()
		const btn = document.querySelector( '#btn-img-prev' )
		if ( btn && btn.style.opacity != '0.3' ) btn.click()
	}
	else if ( ev.key == 'ArrowRight' || ev.key == 'l' )
	{
		ev.preventDefault()
		const btn = document.querySelector( '#btn-img-next' )
		if ( btn && btn.style.opacity != '0.3' ) btn.click()
	}
	else if ( ev.key == ' ' )
	{
		ev.preventDefault()

		if ( Ste && window.currentMdlImgAutoId )
		{
			Ste.toggle( window.currentMdlImgAutoId )

			const {cntTotal, selectedIds} = Ste

			console.log( '[mdlImg Hotkey] Space toggled autoId:', window.currentMdlImgAutoId )

			dsh.syncSte( cntTotal, selectedIds )
		}
	}
	else if ( ev.key == 'Escape' || ev.key == 'q' )
	{
		ev.preventDefault()
		const btn = div.querySelector( '.btn-close' )
		if ( btn ) btn.click()
	}
	else if ( ev.key == 'm' )
	{
		ev.preventDefault()
		const btn = div.querySelector( '#btn-img-mode' )
		if ( btn ) btn.click()
	}
	else if ( ev.key == 'i' )
	{
		ev.preventDefault()
		const btn = div.querySelector( '#btn-img-info' )
		if ( btn ) btn.click()
	}

	else if ( ev.key == '?' )
	{
		ev.preventDefault()
		const btn = div.querySelector( '#btn-img-help' )
		if ( btn ) btn.click()
	}
} )



document.addEventListener( 'DOMContentLoaded', function (){

	//------------------------------------------------
	document.addEventListener( 'click', function ( event ){

		const ste = Ste

		//------------------------------------------------------
		// acts: cbx select status
		//------------------------------------------------------
		if ( event.target.id == 'sim-btn-AllSelect' ){
			event.preventDefault()
			if ( ste ) ste.selectAll()
		}
		if ( event.target.id == 'sim-btn-AllCancel' ){
			event.preventDefault()
			if ( ste ) ste.clearAll()
		}

		//------------------------------------------------------
		// group selection
		//------------------------------------------------------
		if ( event.target.id && event.target.id.startsWith( 'cbx-sel-grp-all-' ) ){
			event.preventDefault()
			const groupId = event.target.id.replace( 'cbx-sel-grp-all-', '' )
			if ( ste ) ste.selectGroup( groupId )
		}
		if ( event.target.id && event.target.id.startsWith( 'cbx-sel-grp-non-' ) ){
			event.preventDefault()
			const groupId = event.target.id.replace( 'cbx-sel-grp-non-', '' )
			if ( ste ) ste.clearGroup( groupId )
		}

		//------------------------------------------------------
		//
		//------------------------------------------------------

	} )

} )


document.addEventListener('DOMContentLoaded', () => {
    const staticContainer = document.body;

    function bindEvts() {
        const sps = document.querySelectorAll('span[class*="tag"]');

        sps.forEach(span => {
            if (!span._hoverEventsBound) {
                span.addEventListener('mouseenter', function() {
                    this.style.opacity = '0.6';
                    this.style.transition = 'opacity 0.3s ease';
                    this.style.cursor = 'pointer'
                });

                span.addEventListener('mouseleave', function() {
                    this.style.opacity = '1';
                    this.style.transition = 'opacity 0.3s ease';
                    this.style.cursor = 'default';
                });
                span._hoverEventsBound = true;
            }
        });
    }

    bindEvts();

    const obs = new MutationObserver(mutations => {
        mutations.forEach(mutation => { if (mutation.type == 'childList') bindEvts() })
    });

    obs.observe(staticContainer, { childList: true, subtree: true });


    staticContainer.addEventListener('click', async (event) => {
        const clickedElement = event.target;

        const targetSpan = clickedElement.closest('span[class*="tag"]');

        if (targetSpan) {
            const textToCopy = targetSpan.textContent;

            if (navigator.clipboard && navigator.clipboard.writeText) {
                try {
                    await navigator.clipboard.writeText(textToCopy);
					console.log('copy: ' + textToCopy);
					notify(`copy! ${textToCopy}`)
                } catch (err) {
                    console.error('copy failed', err);
                }
            } else {
                console.warn('Not support Clipboard API');
                const tempInput = document.createElement('textarea');
                tempInput.value = textToCopy;
                document.body.appendChild(tempInput);
                tempInput.select();
                try {
                    document.execCommand('copy');

					notify(`copy! ${textToCopy}`)
                    console.log('copy!(old) ' + textToCopy);
                } catch (err) {
                    console.error('copy(old) failed', err);
                }
                document.body.removeChild(tempInput);
            }
        }
    });
});

//------------------------------------------------------------------------
// Tab Acts Floating Bar
//------------------------------------------------------------------------
function initTabActsFloating() {
	const tabActs = document.querySelector('.tab-acts');
	if (!tabActs) return;

	let placeholder = document.createElement('div');
	placeholder.className = 'tab-acts-placeholder';
	tabActs.parentNode.insertBefore(placeholder, tabActs.nextSibling);

	let originalTop = null;
	let isFloating = false;

	function updateOriginalTop() {
		if (!isFloating) {
			const rect = tabActs.getBoundingClientRect();
			originalTop = rect.top + window.scrollY;
		}
	}

	function toggleFloatingBar() {
		const currentTab = document.querySelector('.nav-tabs .nav-link.active');
		const isCurrentTab = currentTab && currentTab.textContent.trim() == 'current';
		const scrollY = window.scrollY;

		if (!isCurrentTab) {
			if (isFloating) {
				tabActs.classList.remove('floating', 'show');
				placeholder.classList.remove('active');
				isFloating = false;
			}
			return;
		}

		if (originalTop === null) updateOriginalTop();

		const shouldFloat = scrollY > originalTop + 50;

		if (shouldFloat !== isFloating) {
			if (shouldFloat) {
				tabActs.classList.add('floating');
				placeholder.classList.add('active');
				setTimeout(() => tabActs.classList.add('show'), 10);
				isFloating = true;
			} else {
				tabActs.classList.remove('show');
				setTimeout(() => {
					tabActs.classList.remove('floating');
					placeholder.classList.remove('active');
				}, 300);
				isFloating = false;
			}
		}
	}

	window.addEventListener('scroll', toggleFloatingBar);
	window.addEventListener('resize', () => {
		originalTop = null;
		updateOriginalTop();
	});

	document.addEventListener('click', function(e) {
		if (e.target && e.target.matches('.nav-link')) {
			setTimeout(() => {
				originalTop = null;
				updateOriginalTop();
				toggleFloatingBar();
			}, 100);
		}
	});

	updateOriginalTop();
	setTimeout(toggleFloatingBar, 100);
}

//------------------------------------------------------------------------
// Goto Top Button
//------------------------------------------------------------------------
function initBtnTop(btn) {

	function toggleGotoTopBtn() {
		const currentTab = document.querySelector('.nav-tabs .nav-link.active');
		const isCurrentTab = currentTab && currentTab.textContent.trim() == 'current';
		const scrollY = window.scrollY;

		// console.log('[GotoTop] Toggle check - isCurrentTab:', isCurrentTab, 'scrollY:', scrollY);

		if (isCurrentTab && scrollY > 200) {
			btn.classList.add('show');
			btn.style.display = 'block';
		} else {
			btn.classList.remove('show');
		}
	}

	function scrollToTop() {
		const dst = document.querySelector('#sim-btn-fnd');

		if (dst) {
			dst.scrollIntoView({ behavior: 'smooth', block: 'start' })
		} else {
			// console.warn('[GotoTop] Tab acts element not found, scrolling to top');
			window.scrollTo({ top: 0, behavior: 'smooth' });
		}
	}

	window.addEventListener('scroll', toggleGotoTopBtn);
	btn.addEventListener('click', scrollToTop);

	document.addEventListener('click', function(e) {
		if (e.target && e.target.matches('.nav-link')) setTimeout(toggleGotoTopBtn, 100)
	})

	// Initial check
	toggleGotoTopBtn();
}

document.addEventListener('DOMContentLoaded', function() {
	// Initialize floating tab-acts
	const tabActs = document.querySelector('.tab-acts');
	if (tabActs) {
		console.log('[TabActs] Found tab-acts element, initializing floating behavior');
		initTabActsFloating();
	} else {
		const tabActsObserver = new MutationObserver(function(mutations) {
			const tabActsEl = document.querySelector('.tab-acts');
			if (tabActsEl) {
				console.log('[TabActs] Tab-acts found via observer:', tabActsEl);
				tabActsObserver.disconnect();
				initTabActsFloating();
			}
		});
		tabActsObserver.observe(document.body, { childList: true, subtree: true });
	}

	// Initialize goto top button
	const gotoTopBtn = document.getElementById('sim-goto-top-btn');
	if (!gotoTopBtn) {

		const observer = new MutationObserver(function(mutations) {
			const btn = document.getElementById('sim-goto-top-btn');
			if (btn) {
				console.log('[GotoTop] Button found via observer:', btn);
				observer.disconnect();
				initBtnTop(btn);
			}
		})

		observer.observe(document.body, { childList: true, subtree: true })

		return
	}

	initBtnTop(gotoTopBtn);
})

