// Libraries
import {} from "react";
import { BrowserRouter } from "react-router-dom";
// import io from "socket.io-client";

// Components
import RouterConfig from "./pages/RouterConfig.jsx";

// Styles
import "./App.css";

// CONSTANTS
// import { API_URL } from "./utilities/globals";

// connect

const socket = null //io.connect(API_URL);

// socket.on("connect_failed", function () {
//    document.write("Sorry, there seems to be an issue with the connection!");
// });

function App() {
   return (
      <>
         <div className="App">
            <BrowserRouter basename="/">
               <RouterConfig socket={socket} />
            </BrowserRouter>
         </div>
      </>
   );
}

export default App;
