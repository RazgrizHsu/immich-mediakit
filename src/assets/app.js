window.dash_clientside = window.dash_clientside || {}


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

				let selectedIds = Array.from( window.Ste.selectedIds )
				let totalCount = window.Ste.cntTotal

				let steData = {
					selectedIds: selectedIds,
					cntTotal: totalCount
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
			if ( window.Ste ){
				window.Ste.init( assets.length )

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

			// 直接使用客戶端選擇邏輯，不觸發按鈕點擊
			if ( window.Ste && window.currentMdlImgAutoId )
			{
				window.Ste.toggle( window.currentMdlImgAutoId )

				// 同步到 ste store
				let selectedIds = Array.from( window.Ste.selectedIds )
				let totalCount = window.Ste.cntTotal

				let steData = {
					selectedIds: selectedIds,
					cntTotal: totalCount
				}

				console.log( '[mdlImg Hotkey] Space toggled autoId:', window.currentMdlImgAutoId, 'steData:', steData )

				// 手動觸發 ste store 更新
				if ( window.dash_clientside && window.dash_clientside.set_props )
				{
					window.dash_clientside.set_props( 'store-state', {data: steData} )
				}
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
		console.log( `[Selection] Initialized with ${cnt} assets` )
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

		if ( parentCard )
		{
			if ( isSelected )
				parentCard.classList.add( 'checked' )
			else
				parentCard.classList.remove( 'checked' )
		}

		if ( checkbox ) checkbox.checked = isSelected
	},

	updateButtonStates(){
		const cntSel = this.selectedIds.size
		const cntAll = this.cntTotal
		const cntDiff = cntAll - cntSel

		const btnRm = document.getElementById( 'sim-btn-RmSel' )
		const btnRS = document.getElementById( 'sim-btn-OkSel' )

		if ( btnRm ) btnRm.textContent = `❌ Delete( ${cntSel} ) and ✅ Keep others( ${cntDiff} )`
		if ( btnRS ) btnRS.textContent = `✅ Keep( ${cntSel} ) and ❌ delete others( ${cntDiff} )`


		console.log( `[Selection] Updated buttons - selected: ${cntSel}, total: ${cntAll}` )
	},

	clear(){
		this.selectedIds.clear()
		this.updateAllCardVisuals()
		this.updateButtonStates()
	},

	updateAllCardVisuals(){
		const cards = document.querySelectorAll( '[id*=\'"type":"card-select"\']' )
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
				const match = idStr.match( /"id":"([^"]+)"/ )
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

