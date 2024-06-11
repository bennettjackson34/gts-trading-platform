// Libraries

// Components
import { Button } from "react-bootstrap"

// Hooks
import { useNavigate} from "react-router-dom";

const Home = () => {
    const navigate = useNavigate();
    return(
        <div>
            <div>Home</div>
            <div>
                <Button onClick={()=>navigate("/auth")}>Auth</Button>
                <Button onClick={()=>navigate("/home")}>Home</Button>
                <Button onClick={()=>navigate("/editor")}>Editor</Button>
                <Button onClick={()=>navigate("/analyzer")}>Analyzer</Button>
            </div>
        </div>
    )
}

export default Home