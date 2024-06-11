import { useEffect, useCallback } from "react";
import { Route, Routes, } from "react-router-dom";
import { useNavigate} from "react-router-dom";
import { Toast, ToastContainer } from "react-bootstrap";

// Hooks 
import { useToasts, useToastActions } from "../stores/toasts";
import { useMarketDataActions } from "../stores/marketData";

// Assets 
import notificationSound from "../assets/sounds/notification-sound-1.wav";

// Icons

// API

// Styles 

// Pages
import Home from "../pages/Home";
import Auth from "../pages/Auth";
import Analyzer from "../pages/Analyzer";
import Editor from "../pages/Editor";

// CONSTANTS
// import { API_URL } from "../services/utils/globalVariables";

const ToastSound = new Audio(notificationSound);

const RouterConfig = ({ socket }) => {
	// hooks
	const navigate = useNavigate();
	const toasts = useToasts();
	const { addToast, removeToast } = useToastActions();
	const { updateMarketData } = useMarketDataActions();

	// state

	const handleToastUpdate = useCallback((payload) => {
		addToast(payload);
	}, [])

	const handleMarketDataUpdate = (payload) => {
		updateMarketData(JSON.parse(payload));
	}


	useEffect(() => {
		navigate("/home");
	}, []);
	

	useEffect(() => {
		socket?.on("toast", handleToastUpdate);
		// socket_blpapi.on("market-data:update", handleMarketDataUpdate);
		
		return () => {
			socket?.off("toast", handleToastUpdate);
			// socket_blpapi.off("market-data:update", handleMarketDataUpdate);
			
		}

	}, [socket, handleToastUpdate, handleMarketDataUpdate]);

	return (
		<div className="routerConfig-container">
			<ToastContainer position='top-end'>
				{toasts.map((toast) => {
					return (
						<Toast key={toast.id} bg={toast.variant ?? 'dark'} onEntering={ToastSound.play()} onClose={() => removeToast(toast.id)} delay={toast.delay ?? 5000} autohide>
							<Toast.Header>
								<strong className="me-auto">Notification</strong>
								<small className="text-muted">just now</small>
							</Toast.Header>
							<Toast.Body>{toast.message}</Toast.Body>
						</Toast>
					)
				})}
			</ToastContainer>
			<Routes>
				<Route path="/auth" element={<Auth socket={socket} />} />
				<Route path="/home" element={<Home socket={socket} />} />
                <Route path="/analyzer" element={<Analyzer socket={socket} />} />
                <Route path="/editor" element={<Editor socket={socket} />} />
				{/* List a generic 404-Not Found route here */}
			</Routes>

		</div>
	);
};

export default RouterConfig;