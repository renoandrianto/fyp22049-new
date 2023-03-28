import react from 'react';
// import "assets/css/App.css";
// import 'bootstrap/dist/css/bootstrap.min.css';
// import 'bootstrap/dist/css/bootstrap.min.css';
import StockRow from 'components/StockRow.js';

function App() {
  return (
    <div className="App">
        <div className="container1">
        <table className="table mt-5">
            <thead>
                <tr>
                    <th>Account Number</th>
                    <th>Balance as of</th>
                    <th>Equity</th>
                    <th>Buying Power</th>
                    <th>Cash</th>
                </tr>
            </thead>
            <tbody>
                <StockRow />
            </tbody>
            </table>
        </div>
    </div>
  );
}

export default App;
