import React, {Component} from 'react';
import {iex} from '../configs1/iex.js'

class StockRow extends Component{
    constructor(props){
        super(props)
        this.state = {
            // price: '$5', 
            // qty: 127,
            // marketvalue: "$13030",
            // pf: "+$900"
            data:{}
        }
    }
    componentDidMount(){
        //query the api
        // const url = `${iex.base_url}/stock/${this.props.ticker}/intraday-prices?chartLast=1&token=${iex.api_token}`
        const url = `${iex.base_url}/v2/account`
        fetch(url, {
            headers: {
               "Apca-Api-Key-Id": iex.api_token,
               "Apca-Api-Secret-Key": iex.api_secret_key
            }
        })
        .then((response)=>response.json())
        .then((data) => {
            console.log(data)
            this.setState({
                data:data
            })
        })
    }


    render() {
        return (
            <tr>
                {/* <td> {this.props.column}</td> */}
                <td>{this.state.data.account_number} </td>
                <td> {this.state.data.balance_asof}</td>
                <td>{this.state.data.last_equity} </td>
                <td>{this.state.data.buying_power} </td>
                <td>{this.state.data.cash} </td>
            </tr>
        )
    }
}
export default StockRow;