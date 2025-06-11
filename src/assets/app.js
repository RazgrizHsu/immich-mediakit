window.dash_clientside = window.dash_clientside || {}


//
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


//------------------------------------------------------------------------
// similar
//------------------------------------------------------------------------
window.dash_clientside.similar = {

	//------------------------------------
	onCardSelectClicked( n_clicks ){
		if ( dash_clientside.callback_context.triggered.length > 0 ){
			let triggered = dash_clientside.callback_context.triggered[ 0 ]
			if ( triggered.prop_id && triggered.value > 0 ){
				let triggeredId = JSON.parse( triggered.prop_id.split( '.' )[ 0 ] )
				window.Ste.toggle( triggeredId.id )

				let steData = {
					cntTotal: window.Ste.cntTotal,
					selectedIds: Array.from( window.Ste.selectedIds ),
				}

				console.log( '[Selection] Syncing to ste store on selection:', steData )
				return steData
			}
		}
		return dash_clientside.no_update
	},

	onNowSyncToDummyInit( now_data ){
		if ( now_data && now_data.sim && now_data.sim.assCur ){
			let assets = now_data.sim.assCur
			if ( window.Ste ) window.Ste.init( assets.length )
		}
		return dash_clientside.no_update
	}
}

//------------------------------------------------------------------------
// mdlImg Client State Manager
//------------------------------------------------------------------------
window.MdlImgClient = {
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

		if ( direction === 'prev' && newIdx > 0 ){
			newIdx = newIdx - 1
		}
		else if ( direction === 'next' && newIdx < assets.length - 1 ){
			newIdx = newIdx + 1
		}
		else{
			return this.noUpdate( 6 )
		}

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

		console.log( `[MdlImgClient] navigated to idx[${newIdx}] autoId[${curAss.autoId}]` )

		return [newMdl, htms, prevStyle, nextStyle, selectText, selectColor]
	},

	buildImageContent( mdl ){
		const htms = []

		if ( mdl.imgUrl ){
			htms.push( React.createElement( 'img', {src: mdl.imgUrl} ) )
		}

		if ( mdl.isMulti && this.state.now?.sim?.assCur && mdl.curIdx < this.state.now.sim.assCur.length ){
			const ass = this.state.now.sim.assCur[ mdl.curIdx ]
			if ( ass ){
				htms.push(
					React.createElement( 'div', {className: 'acts B'},
						React.createElement( 'span', {className: 'tag xl'},
							`#${ass.autoId} @${ass.simGIDs?.join( ',' ) || ''}`
						)
					)
				)
			}
		}

		return htms
	},

	getPrevButtonStyle( mdl ){
		if ( !mdl.isMulti || !this.state.now?.sim?.assCur || this.state.now.sim.assCur.length <= 1 ){
			return {display: 'none'}
		}
		return {
			display: 'block',
			opacity: mdl.curIdx <= 0 ? '0.3' : '1'
		}
	},

	getNextButtonStyle( mdl ){
		if ( !mdl.isMulti || !this.state.now?.sim?.assCur || this.state.now.sim.assCur.length <= 1 ){
			return {display: 'none'}
		}
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

	noUpdate( count ){
		return Array( count ).fill( dash_clientside.no_update )
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

		const curAsset = this.getCurrentAsset()
		if ( !curAsset ) return []

		const assetRows = [
			React.createElement( 'tr', {},
				React.createElement( 'td', {}, 'autoId' ),
				React.createElement( 'td', {},
					React.createElement( 'span', {className: 'tag'}, `#${curAsset.autoId}` ),
					React.createElement( 'span', {className: 'tag'}, `@${curAsset.simGIDs?.join( ',' ) || ''}` )
				)
			),
			React.createElement( 'tr', {},
				React.createElement( 'td', {}, 'id' ),
				React.createElement( 'td', {}, React.createElement( 'span', {className: 'tag sm second'}, curAsset.id ) )
			),
			React.createElement( 'tr', {},
				React.createElement( 'td', {}, 'Filename' ),
				React.createElement( 'td', {}, curAsset.originalFileName )
			)
		]

		const exifRows = this.buildExifRows( curAsset )
		const allRows = [...assetRows, ...exifRows]

		return React.createElement( 'table', {className: 'table-sm table-striped', style: {width: '100%'}},
			React.createElement( 'tbody', {}, ...allRows )
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

				if ( key === "fileSizeInByte" ){
					displayValue = this.formatFileSize( value )
				}
				else if ( key === "focalLength" && typeof value === 'number' ){
					displayValue = `${value} mm`
				}
				else if ( key === "fNumber" && typeof value === 'number' ){
					displayValue = `f/${value}`
				}
				else if ( value ){
					displayValue = this.formatDate( value )
				}

				if ( displayValue ){
					rows.push(
						React.createElement( 'tr', {},
							React.createElement( 'td', {}, displayKey ),
							React.createElement( 'td', {}, displayValue )
						)
					)
				}
			}
		}

		return rows
	},

	formatFileSize( value ){
		if ( typeof value === 'number' ){
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
			if ( parts.length === 2 && parts[ 1 ].includes( '+' ) ){
				const timePart = parts[ 1 ]
				if ( timePart.includes( '.' ) && ( timePart.includes( '+' ) || timePart.includes( '-' ) ) ){
					const timeParts = timePart.split( '.' )
					if ( timeParts.length === 2 ){
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
			newCss = currentClasses.split( ' ' ).filter( c => c !== 'auto' ).join( ' ' )
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

						if ( window.Ste ){
							window.Ste.toggle( autoId )

							let selectedIds = Array.from( window.Ste.selectedIds )
							let totalCount = window.Ste.cntTotal

							let steData = {
								selectedIds: selectedIds,
								cntTotal: totalCount
							}

							console.log( '[mdlImg Selection] Toggled autoId:', autoId, 'steData:', steData )
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

		MdlImgClient.init( mdlData, nowData, steData )

		const trigId = ctx.triggered[ 0 ].prop_id
		if ( trigId.includes( 'btn-img-prev' ) ){
			return MdlImgClient.navigate( 'prev' )
		}
		else if ( trigId.includes( 'btn-img-next' ) ){
			return MdlImgClient.navigate( 'next' )
		}

		return dash_clientside.no_update
	},

	onContentUpdate( mdlData, nowData, steData ){
		MdlImgClient.init( mdlData, nowData, steData )
		return MdlImgClient.updateModalContent()
	},

	onHelpToggle( nClicks, mdlData ){
		if ( !nClicks ) return Array( 3 ).fill( dash_clientside.no_update )

		MdlImgClient.init( mdlData, null, null )
		return MdlImgClient.toggleHelp()
	},

	onInfoToggle( nClicks, mdlData ){
		if ( !nClicks ) return Array( 3 ).fill( dash_clientside.no_update )

		MdlImgClient.init( mdlData, null, null )
		return MdlImgClient.toggleInfo()
	},

	onModeToggle( nClicks, currentClasses ){
		if ( !nClicks ) return Array( 2 ).fill( dash_clientside.no_update )

		return MdlImgClient.toggleMode( currentClasses )
	},

	onSteChanged( steData, nowData, mdlData ){
		if ( !steData || !nowData || !mdlData ) return Array( 2 ).fill( dash_clientside.no_update )

		MdlImgClient.init( mdlData, nowData, steData )

		if ( !mdlData.isMulti || !nowData.sim?.assCur || mdlData.curIdx >= nowData.sim.assCur.length ){
			return Array( 2 ).fill( dash_clientside.no_update )
		}

		const curAss = nowData.sim.assCur[ mdlData.curIdx ]
		if ( !curAss ) return Array( 2 ).fill( dash_clientside.no_update )

		const selectText = MdlImgClient.getSelectButtonText( mdlData, curAss )
		const selectColor = MdlImgClient.getSelectButtonColor( mdlData, curAss )

		console.log( `[MdlImgClient] Updated button state for autoId[${curAss.autoId}]` )

		return [selectText, selectColor]
	}

}

//------------------------------------------------------------------------
// global
//------------------------------------------------------------------------
document.addEventListener( 'keydown', function ( ev ){
	const modal = document.querySelector( '#img-modal' )

	if ( modal && modal.parentElement.classList.contains( 'show' ) )
	{
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

			if ( window.Ste && window.currentMdlImgAutoId )
			{
				window.Ste.toggle( window.currentMdlImgAutoId )

				const {cntTotal, selectedIds} = window.Ste

				console.log( '[mdlImg Hotkey] Space toggled autoId:', window.currentMdlImgAutoId )

				dsh.syncSte( cntTotal, selectedIds )
			}
		}
		else if ( ev.key == 'Escape' || ev.key == 'q' )
		{
			ev.preventDefault()
			const btn = modal.querySelector( '.btn-close' )
			if ( btn ) btn.click()
		}
		else if ( ev.key == 'm' )
		{
			ev.preventDefault()
			const btn = modal.querySelector( '#btn-img-mode' )
			if ( btn ) btn.click()
		}
		else if ( ev.key == 'i' )
		{
			ev.preventDefault()
			const btn = modal.querySelector( '#btn-img-info' )
			if ( btn ) btn.click()
		}

		else if ( ev.key == '?' )
		{
			ev.preventDefault()
			const btn = modal.querySelector( '#btn-img-help' )
			if ( btn ) btn.click()
		}
	}
} )


window.Ste = {
	cntTotal: 0,
	selectedIds: new Set(),

	init( cnt ){
		this.cntTotal = cnt
		this.selectedIds.clear()
		console.log( `[Selection] Initialized with ${cnt} assets, selected[ ${this.selectedIds.size} ]` )

		dsh.syncSte( this.cntTotal, this.selectedIds )
	},

	toggle( aid ){
		if ( this.selectedIds.has( aid ) )
			this.selectedIds.delete( aid )
		else
			this.selectedIds.add( aid )

		console.log( `[Selection] Toggled ${aid}, selected count: ${this.selectedIds.size}` )

		this.updateCardVisual( aid )
		this.updateButtonStates()
	},

	updateCardVisual( aid ){
		const card = document.querySelector( `[id*='"type":"card-select"'][id*='"id":${aid}']` )
		if ( !card ){
			console.error( `[Selection] No cards found for ${aid}` )
			return
		}

		const parentCard = card.closest( '.card' )
		const checkbox = card.querySelector( 'input[type="checkbox"]' )
		const isSelected = this.selectedIds.has( aid )

		//console.log( `[Selection] updateCardVisual ${aid}: isSelected=${isSelected}, parentCard=${!!parentCard}, checkbox=${!!checkbox}` )

		if ( parentCard ) parentCard.classList[ isSelected ? 'add' : 'remove' ]( 'checked' )

		if ( checkbox ) checkbox.checked = isSelected
	},

	updateButtonStates(){
		const cntSel = this.selectedIds.size
		const cntAll = this.cntTotal
		const cntDiff = cntAll - cntSel

		const btnRm = document.getElementById( 'sim-btn-RmSel' )
		const btnRS = document.getElementById( 'sim-btn-OkSel' )
		const btnAllSelect = document.getElementById( 'sim-btn-AllSelect' )
		const btnAllCancel = document.getElementById( 'sim-btn-AllCancel' )

		if ( btnRm ) btnRm.textContent = `❌ Delete( ${cntSel} ) and ✅ Keep others( ${cntDiff} )`
		if ( btnRS ) btnRS.textContent = `✅ Keep( ${cntSel} ) and ❌ delete others( ${cntDiff} )`

		if ( btnAllSelect ) btnAllSelect.disabled = ( cntSel >= cntAll || cntAll === 0 )
		if ( btnAllCancel ) btnAllCancel.disabled = ( cntSel === 0 )

		console.log( `[Selection] Updated buttons - selected: ${cntSel}, total: ${cntAll}` )
	},

	selectAll(){
		const cards = document.querySelectorAll( '[id*="card-select"]' )
		cards.forEach( card => {
			const assetId = this.extractAssetIdFromElement( card )
			if ( assetId ) this.selectedIds.add( assetId )
		} )
		this.updateAllCardVisuals()
		this.updateButtonStates()
		console.log( `[Selection] Selected all ${this.selectedIds.size} assets` )
	},

	clearAll(){
		this.selectedIds.clear()
		this.updateAllCardVisuals()
		this.updateButtonStates()
		console.log( `[Selection] Cleared all selections` )
	},

	updateAllCardVisuals(){
		const cards = document.querySelectorAll( '[id*="card-select"]' )
		console.log( `[Selection] updateAllCardVisuals found ${cards.length} cards` )
		cards.forEach( card => {
			const assetId = this.extractAssetIdFromElement( card )
			if ( assetId ) this.updateCardVisual( assetId )
		} )
	},

	extractAssetIdFromElement( element ){
		try{
			const idStr = element.getAttribute( 'id' )
			if ( idStr && idStr.includes( 'card-select' ) )
			{
				const match = idStr.match( /"id":(\d+)/ )
				return match ? match[ 1 ] : null
			}
		}
		catch ( e )
		{
			console.error( '[Selection] Error extracting asset ID:', e )
		}
		return null
	},
}

window.handleCardSelect = function ( trigger ){
	try{
		const triggeredId = trigger.triggered_id
		if ( triggeredId && triggeredId.type === 'card-select' )
		{
			const assetId = triggeredId.id
			window.Ste.toggle( assetId )
			return window.dash_clientside.no_update
		}
	}
	catch ( e )
	{
		console.error( '[Selection] Error in handleCardSelect:', e )
	}

	return window.dash_clientside.no_update
}

document.addEventListener( 'DOMContentLoaded', function (){

	//------------------------------------------------
	document.addEventListener( 'click', function ( event ){

		const ste = window.ste

		//------------------------------------------------------
		// acts: cbx select status
		//------------------------------------------------------
		if ( event.target.id === 'sim-btn-AllSelect' ){
			event.preventDefault()
			if ( ste ) ste.selectAll()
		}
		if ( event.target.id === 'sim-btn-AllCancel' ){
			event.preventDefault()
			if ( ste ) ste.clearAll()
		}

		//------------------------------------------------------
		//
		//------------------------------------------------------

	} )
} )

