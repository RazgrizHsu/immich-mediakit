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
			const btn = document.querySelector( '#btn-img-select' )
			if ( btn && btn.style.display !== 'none' ) btn.click()
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

