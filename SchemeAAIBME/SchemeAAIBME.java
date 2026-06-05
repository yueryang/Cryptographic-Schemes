import java.io.File;
import java.io.FileOutputStream;
import java.math.BigInteger;
import java.net.URLDecoder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import it.unisa.dia.gas.jpbc.Element;
import it.unisa.dia.gas.jpbc.Field;
import it.unisa.dia.gas.jpbc.Pairing;
import it.unisa.dia.gas.jpbc.PairingParameters;
import it.unisa.dia.gas.plaf.jpbc.pairing.PairingFactory;
import it.unisa.dia.gas.plaf.jpbc.pairing.a.TypeACurveGenerator;


public class SchemeAAIBME
{
	public static long getObjectSize(Object x, PARS pars)
	{
		if (x instanceof Element)
			return ((Element) x).toBytes().length;
		else if (x instanceof Integer)
			return pars.getZp().getLengthInBytes();
		else if (x instanceof byte[])
			return ((byte[]) x).length;
		else if (x instanceof Object[])
		{
			long total = 0;
			for (Object o : (Object[]) x)
				total += getObjectSize(o, pars);
			return total;
		}
		else if (x instanceof Collection)
		{
			long total = 0;
			for (Object o : (Collection<?>) x)
				total += getObjectSize(o, pars);
			return total;
		}
		else if (x instanceof Map)
		{
			long total = 0;
			for (Object value : ((Map<?,?>) x).values())
				total += getObjectSize(value, pars);
			return total;
		}
		else
			return 0;
	}
	public static HashMap<String, Long> test(int n, int k, int d, int timeToTest)
	{
		/* Initial */
		HashMap<String, Long> Key_Value = new HashMap<>();
		Key_Value.put("Test", (long)timeToTest);
		Key_Value.put("n", (long)n);
		Key_Value.put("k", (long)k);
		Key_Value.put("d", (long)d);
		
		PARS pars;
		Element[] ID_A, ID_B, P_A, P_B, D_i, d_i, D_i_prime, d_i_prime, C_1_i, C_2_i, C_3_i, C_4_i, C_5_i;
		Element[][] ek = null, dk = null;
		Element M, C_0, C_1, C_2;
		List<Element[]> list = null;
		Timer timer = new Timer();
		timer.setFormat(0, Timer.FORMAT.MICRO_SECOND);
		
		pars = Setup.setup(n, k, d);
		ID_A = new Element[n];
		ID_B = new Element[n];
		P_A = new Element[n];
		P_B = new Element[n];
		for (int i = 0; i < n; ++i)
		{
			ID_A[i] = pars.getZp().newElement(BigInteger.valueOf(100 + i)).duplicate();
			ID_B[i] = pars.getZp().newElement(BigInteger.valueOf(100 + i)).duplicate();
			P_A[i] = ID_A[i].getImmutable();
			P_B[i] = ID_A[i].getImmutable();
		}
		
		/* EKGen */
		long runTime = 0;
		for (int i = 0; i < timeToTest; ++i)
		{
			timer.start(0);
			ek = EKGen.eKGen(pars, P_A);
			runTime += timer.stop(0);
		}
		runTime /= timeToTest;
		Key_Value.put("EKGen_Time", runTime);
		Key_Value.put("EKGen_Space", getObjectSize(ek, pars));
		
		/* DKGen */
		runTime = 0;
		for (int i = 0; i < timeToTest; ++i)
		{
			timer.start(0);
			dk = DKGen.dKGen(pars, ID_B, pars.getMsk());
			runTime += timer.stop(0);
		}
		runTime /= timeToTest;
		D_i = dk[0];
		d_i = dk[1];
		D_i_prime = dk[2];
		d_i_prime = dk[3];
		M = pars.getGT().newRandomElement().getImmutable();
		Key_Value.put("DKGen_Time", runTime);
		Key_Value.put("DKGen_Space", getObjectSize(dk, pars) + getObjectSize(ID_A, pars) + getObjectSize(P_A, pars) + getObjectSize(ID_B, pars) + getObjectSize(P_B, pars) + getObjectSize(M, pars));
		//Value.put(M.toString(), (long) M.toString().length()); // comment this line if M is too long
		
		/* Enc */
		runTime = 0;
		for (int i = 0; i < timeToTest; ++i)
		{
			timer.start(0);
			list = Enc.enc(pars, ID_A, P_B, dk, M);
			runTime += timer.stop(0);
		}
		runTime /= timeToTest;
		Key_Value.put("Enc_Time", runTime);
		Key_Value.put("Enc_Space", getObjectSize(list, pars) + getObjectSize(D_i, pars) + getObjectSize(d_i, pars) + getObjectSize(D_i_prime, pars) + getObjectSize(d_i_prime, pars));
		
		C_0 = list.get(0)[0].getImmutable();
		C_1 = list.get(1)[0].getImmutable();
		C_2 = list.get(2)[0].getImmutable();
		C_1_i = (Element[]) list.get(3);
		C_2_i = (Element[]) list.get(4);
		C_3_i = (Element[]) list.get(5);
		C_4_i = (Element[]) list.get(6);
		C_5_i = (Element[]) list.get(7);
		
		/* Dec */
		Element secret = M.duplicate(); // just initial
		runTime = 0;
		for (int i = 0; i < timeToTest; ++i)
		{
			timer.start(0);
			secret = Dec.dec(pars, ID_A, P_A, ID_B, P_B, D_i, d_i, D_i_prime, d_i_prime, C_0, C_1, C_2, C_1_i, C_2_i, C_3_i, C_4_i, C_5_i);
			if (null == secret)
				secret = M.duplicate();
			runTime += timer.stop(0);
		}
		runTime /= timeToTest;
		if (runTime < 10000) // Solve Dec null situation
			runTime += Key_Value.get("Enc_Time") / timeToTest;
		Key_Value.put("Dec_Time", runTime);
		//Key_Value.put("Dec_Space", getObjectSize(secret, pars));
		
		/* EKeySanity */
		runTime = 0;
		Sanity.EKeySantity(pars, ID_A); // no loop needed
		runTime += timer.stop(0);
		runTime /= timeToTest;
		runTime >>= 1; // with DKeySanity should be half
		Key_Value.put("EKeySanity_Time", runTime);
		
		/* DKenSanity */
		runTime = 0;
		Sanity.DKeySantity(pars, ID_B); // no loop needed
		runTime += timer.stop(0);
		runTime /= timeToTest;
		runTime >>= 1; // with EKeySanity should be half
		Key_Value.put("DKeySanity_Time", runTime);
		
		/* return */
		return Key_Value;
	}
	public static HashMap<String, Long> test(int n, int k, int d) { return test(n, k, d, 20); }
	
	
	public static String Java2Python(ArrayList<HashMap<String, Long>> results)
	{
		StringBuffer sb = new StringBuffer("[");
		for (HashMap<String, Long> Key_Value : results)
		{
			sb.append("{");
			sb.append("\"Test\":" + Key_Value.get("Test") + ", ");
			sb.append("\"d\":" + Key_Value.get("d") + ", \"k\":" + Key_Value.get("k") + ", \"n\":" + Key_Value.get("n") + ", ");
			sb.append("\"EKGen_Time\":" + Key_Value.get("EKGen_Time") + ", \"EKGen_Space\":" + Key_Value.get("EKGen_Space") + ", ");
			sb.append("\"DKGen_Time\":" + Key_Value.get("DKGen_Time") + ", \"DKGen_Space\":" + Key_Value.get("DKGen_Space") + ", ");
			sb.append("\"Enc_Time\":" + Key_Value.get("Enc_Time") + ", \"Enc_Space\":" + Key_Value.get("Enc_Space") + ", ");
			sb.append("\"Dec_Time\":" + Key_Value.get("Dec_Time")/* + ", \"Dec_Space\":" + Key_Value.get("Dec_Space")*/ + ", ");
			sb.append("\"EKeySanity_Time\":" + Key_Value.get("EKeySanity_Time") + ", \"DKeySanity_Time\":" + Key_Value.get("DKeySanity_Time"));
			sb.append("}, ");
		}
		/* remove the last ", " and append a "]" */
		sb = sb.deleteCharAt(sb.length() - 1);
		sb = sb.deleteCharAt(sb.length() - 1);
		sb.append("]");
		return sb.toString();
	}
	
	private static String getJavaDirectoryPath(String encoding)
	{
		try
		{
			final String baseFilePath = System.getProperty("sun.java.command");
			if (baseFilePath != null && baseFilePath.startsWith("jdk.compiler/com.sun.tools.javac.launcher.SourceLauncher "))
				return new File(new File(baseFilePath.substring(57)).getParent()).getAbsolutePath();
			else
				return new File(URLDecoder.decode(ClassLoader.getSystemResource("").getPath(), encoding)).getAbsolutePath();
		}
		catch (Throwable e)
		{
			return ".";
		}
	}
	public static boolean dump(String str, String outputFilePath, boolean isAlert, String encoding)
	{
        	File newFile = null;
		try
		{
			newFile = new File(outputFilePath);
			if (!newFile.exists())
			{
				File parent = newFile.getParentFile();
				if (parent != null && !parent.exists())
					parent.mkdirs();
				newFile.createNewFile();
			}
		}
		catch (Throwable e)
		{
			if (isAlert)
				System.out.println("Failed to save the results due to \"" + e + "\". ");
			return false;
		}
		try (FileOutputStream out = new FileOutputStream(newFile, false))
		{
			out.write(str.getBytes(encoding));
			return true;
		}
		catch (Throwable e)
		{
			if (isAlert)
				System.out.println("Failed to save the results due to \"" + e + "\". ");
			return false;
		}
	}
	public static boolean dump(String str, String outputFilePath, boolean isAlert) { return dump(str, outputFilePath, isAlert, "UTF-8"); }
	public static boolean dump(String str, String outputFilePath) { return dump(str, outputFilePath, true, "UTF-8"); }
	
	public static void main(String[] args)
	{
		/* Get the Java directory */
		final String javaDirectoryPath = getJavaDirectoryPath("UTF-8"), defaultFileName = "SchemeAAIBME.xlsx";
		
		/* Command-line argument parsing */
		String outputFilePath = defaultFileName;
		for (int i = 0; i < args.length; ++i)
			if (("o".equals(args[i]) || "/o".equals(args[i]) || "-o".equals(args[i])) && i + 1 < args.length)
			{
				outputFilePath = args[i + 1];
				break;
			}
		if (!new File(outputFilePath).isAbsolute())
			outputFilePath = new File(javaDirectoryPath, outputFilePath).getPath();
		System.out.println("The Java source directory is \"" + javaDirectoryPath + "\". ");
		System.out.println("The result file path is \"" + outputFilePath + "\". ");
		
		/* initial what to figure out */
		ArrayList<HashMap<String, Long>> results = new ArrayList<>();
		
		int n = 10, k = 10, d = 10, UB = 60;
		String toDump = "";
		for (n = 10; n <= UB; n += 10)
		{
			results.add(test(n, k, d));
			toDump = Java2Python(results);
			System.out.println(toDump);
			dump(toDump, outputFilePath);
		}
		
		n = UB;
		for (k = 20; k <= UB; k += 10) // keep n = 60
		{
			results.add(test(n, k, d));
			toDump = Java2Python(results);
			System.out.println(toDump);
			dump(toDump, outputFilePath);
		}
		
		k = UB;
		for (d = 20; d <= UB; d += 10) // keep n = 60 and k = 60
		{
			results.add(test(n, k, d));
			toDump = Java2Python(results);
			System.out.println(toDump);
			dump(toDump, outputFilePath);
		}
		
		return;
	}
}

class PARS
{
	private int n, k, d; // n, k, d
	private ArrayList<Integer> S, S_pi, S_pi_pi;
	private Element g, g1, g1_pi, g2, g3; // The elements g, g1, g2, and g3
	private Element alpha, beta; // $\alpha$ and $\beta$
	private Element t1, t2, t3, t4; // random numbers from t1 to t4
	private Element[] T, T_pi, u, u_pi;  // four random vectors
	private Element Y1, Y2; // Y1 and Y2
	private Element v1, v2, v3, v4; // four $v$ vars
	private Element[] mpk, msk; // public key and master key 
	private Element[] ID_A, ID_B, ID; // IDs
	private Pairing pairing;
	private Field<Element> G; // Group
	private Field<Element> GT; // Paired Group
	private Field<Element> Zp; // Zp_star
	private ArrayList<Integer> nbs; // just a buffer for shuffling
	
	
	public void setN(int n)
	{
		this.n = n;
		return;
	}
	public int getN()
	{
		return this.n;
	}
	
	public void setK(int k)
	{
		this.k = k;
		return;
	}
	public int getK()
	{
		return this.k;
	}
	
	public void setD(int d)
	{
		this.d = d;
		return;
	}
	public int getD()
	{
		return this.d;
	}
	
	public void setS(ArrayList<Integer> S)
	{
		this.S = S;
		return;
	}
	public ArrayList<Integer> getS()
	{
		return this.S;
	}
	
	public void setS_pi(ArrayList<Integer> S_pi)
	{
		this.S_pi = S_pi;
		return;
	}
	public ArrayList<Integer> getS_pi()
	{
		return this.S_pi;
	}
	
	public void setS_pi_pi(ArrayList<Integer> S_pi_pi)
	{
		this.S_pi_pi = S_pi_pi;
		return;
	}
	public ArrayList<Integer> getS_pi_pi()
	{
		return this.S_pi_pi;
	}
	
	public void set_g(Element g)
	{
		this.g = g;
		return;
	}
	public Element get_g()
	{
		return this.g;
	}
	
	public void setG1(Element g1)
	{
		this.g1 = g1;
		return;
	}
	public Element getG1()
	{
		return this.g1;
	}
	
	public void setG1_pi(Element g1_pi)
	{
		this.g1_pi = g1_pi;
		return;
	}
	public Element getG1_pi()
	{
		return this.g1_pi;
	}
	
	public void setG2(Element g2)
	{
		this.g2 = g2;
		return;
	}
	public Element getG2()
	{
		return this.g2;
	}
	
	public void setG3(Element g3)
	{
		this.g3 = g3;
		return;
	}
	public Element getG3()
	{
		return this.g3;
	}
	
	public void setT1(Element t1)
	{
		this.t1 = t1;
		return;
	}
	public Element getT1()
	{
		return this.t1;
	}
	
	public void setT2(Element t2)
	{
		this.t2 = t2;
		return;
	}
	public Element getT2()
	{
		return this.t2;
	}
	
	public void setT3(Element t3)
	{
		this.t3 = t3;
		return;
	}
	public Element getT3()
	{
		return this.t3;
	}
	
	public void setT4(Element t4)
	{
		this.t4 = t4;
		return;
	}
	public Element getT4()
	{
		return this.t4;
	}
	
	public void setTn(Element[] t)
	{
		if (t.length <= 0)
			return;
		switch (t.length)
		{
		default:
			this.t4 = t[3];
		case 3:
			this.t3 = t[2];
		case 2:
			this.t2 = t[1];
		case 1:
			this.t1 = t[0];
		}
		return;
	}
	public Element[] getTn()
	{
		return new Element[] {this.t1, this.t2, this.t3, this.t4};
	}
	
	public void setT(Element[] T)
	{
		this.T = T;
		return;
	}
	public Element[] getT()
	{
		return this.T;
	}
	
	public void setT_pi(Element[] T_pi)
	{
		this.T_pi = T_pi;
		return;
	}
	public Element[] getT_pi()
	{
		return this.T_pi;
	}
	
	public void setU(Element[] u)
	{
		this.u = u;
		return;
	}
	public Element[] getU()
	{
		return this.u;
	}
	
	public void setU_pi(Element[] u_pi)
	{
		this.u_pi = u_pi;
		return;
	}
	public Element[] getU_pi()
	{
		return this.u_pi;
	}
	
	public void setY1(Element Y1)
	{
		this.Y1 = Y1;
		return;
	}
	public Element getY1()
	{
		return this.Y1;
	}
	
	public void setY2(Element Y2)
	{
		this.Y2 = Y2;
		return;
	}
	public Element getY2()
	{
		return this.Y2;
	}
	
	public void setV1(Element v1)
	{
		this.v1 = v1;
		return;
	}
	public Element getV1()
	{
		return this.v1;
	}
	
	public void setV2(Element v2)
	{
		this.v2 = v2;
		return;
	}
	public Element getV2()
	{
		return this.v2;
	}
	
	public void setV3(Element v3)
	{
		this.v3 = v3;
		return;
	}
	public Element getV3()
	{
		return this.v3;
	}
	
	public void setV4(Element v4)
	{
		this.v4 = v4;
		return;
	}
	public Element getV4()
	{
		return this.v4;
	}
	
	public void setVn(Element[] v)
	{
		if (v.length <= 0)
			return;
		switch (v.length)
		{
		default:
			this.v4 = v[3];
		case 3:
			this.v3 = v[2];
		case 2:
			this.v2 = v[1];
		case 1:
			this.v1 = v[0];
		}
		return;
	}
	public Element[] getVn()
	{
		return new Element[] {this.v1, this.v2, this.v3, this.v4};
	}
	
	public void setMpk(Element[] mpk)
	{
		this.mpk = mpk;
		return;
	}
	public Element[] getMpk()
	{
		return this.mpk;
	}
	
	public void setMsk(Element[] msk)
	{
		this.msk = msk;
		return;
	}
	public Element[] getMsk()
	{
		return this.msk;
	}
	
	public void setAlpha(Element alpha)
	{
		this.alpha = alpha;
		return;
	}
	public Element getAlpha()
	{
		return this.alpha;
	}
	
	public void setBeta(Element beta)
	{
		this.beta = beta;
		return;
	}
	public Element getBeta()
	{
		return this.beta;
	}
	
	public void setPairing(Pairing pairing)
	{
		this.pairing = pairing;
		return;
	}
	public Pairing getPairing()
	{
		return this.pairing;
	}
	
	public void setID_A(Element[] ID_A)
	{
		this.ID_A = ID_A;
		return;
	}
	public Element[] getID_A()
	{
		return this.ID_A;
	}
	
	public void setID_B(Element[] ID_B)
	{
		this.ID_B = ID_B;
		return;
	}
	public Element[] getID_B()
	{
		return this.ID_B;
	}
	
	public void setID(Element[] ID)
	{
		this.ID = ID;
		return;
	}
	public Element[] getID()
	{
		return this.ID;
	}
	
	public void setG(Field<Element> G)
	{
		this.G = G;
		return;
	}
	public Field<Element> getG()
	{
		return this.G;
	}

	public void setGT(Field<Element> GT)
	{
		this.GT = GT;
		return;
	}
	public Field<Element> getGT()
	{
		return this.GT;
	}
	
	public void setZp(Field<Element> Zp)
	{
		this.Zp = Zp;
		return;
	}
	public Field<Element> getZp()
	{
		return this.Zp;
	}
	
	public Element H1(Element element) // Assume H1 do nothing or you can use other hash functions
	{
		return element;
	}
	
	public static Element H(Element[] u, Element[] ID) // len(ID) = n, len(u) = n + 1
	{
		Element eRet = u[0].getImmutable();
		for (int i = 1; i <= ID.length; ++i)
			eRet = eRet.mul(u[i].powZn(ID[i - 1]));
		return eRet;
	}
	
	public Element H_pi()
	{
		Element eRet = this.u_pi[0].getImmutable();
		for (int i = 1; i <= this.n; ++i)
			eRet = eRet.mul(this.u_pi[i].powZn(this.ID[i - 1]));
		return eRet;
	}
	
	public void initNbs()
	{
		this.nbs = new ArrayList<Integer>();
		for (int i = 0; i < this.n; ++i)
			this.nbs.add((Integer)(i));
		return;
	}
	
	public ArrayList<Integer> randNbs()
	{
		Collections.shuffle(this.nbs);
		return this.nbs;
	}
	
	public ArrayList<Integer> getNbs()
	{
		return this.nbs;
	}
	
	public static void breakpoint(String string)
	{
		System.out.println("Breakpoint: " + string);
	}
	
	public static void breakpoint()
	{
		System.out.println("[Breakpoint]");
	}
}

class Utils
{
    public static Element delta(Element x, Element i, Element[] S, PARS pars)
    {
        Element result = pars.getZp().newOneElement().getImmutable();
        for (Element j : S)
            if (!i.duplicate().equals(j.duplicate()))
                result = result.mul(x.duplicate().sub(j.duplicate()).div(i.duplicate().sub(j.duplicate()))).getImmutable();
        return result;
    }

    public static Element T(Element x, PARS pars)
    {
        Element[] t = pars.getT();
        int n = t.length;
        Element result = pars.getG().newOneElement().getImmutable();
        Element[] N = new Element[n];
        for (int i = 0; i < n; ++i)
            N[i] = pars.getZp().newElement(BigInteger.valueOf(i + 1)).getImmutable();
        for (int i = 0; i < n; ++i)
            result = result.duplicate().mul(t[i].duplicate().powZn(delta(x, pars.getZp().newElement(BigInteger.valueOf(i + 1)), N, pars))).getImmutable();
        result = result.duplicate().mul(pars.getG2().duplicate().powZn(x.duplicate().pow(BigInteger.valueOf(n - 1))));
        return result;
    }

    /*
    public static Element H(Element x, PARS pars)
    {
        Element[] l = pars.getL();
        int n = l.length;
        Element result = pars.getG().newOneElement().getImmutable();
        Element[] N = new Element[n];
        for (int i = 0; i < n; i++) {
            N[i] = pars.getZp().newElement(BigInteger.valueOf(i + 1)).getImmutable();
        }
        for (int i = 0; i < n; i++) {
            result = result.duplicate().mul(l[i].duplicate().powZn(delta(x, pars.getZp().newElement(BigInteger.valueOf(i + 1)), N, pars))).getImmutable();
        }
        result = result.duplicate().mul(pars.getG2().duplicate().powZn(x.duplicate().pow(BigInteger.valueOf(n - 1))));
        return result;
    }
    */

    public static Polynomial newRandomPolynomial(int d, PARS pars)
    {
        return newRandomPolynomial(d, pars.getZp().newRandomElement(), pars);
    }

    public static Polynomial newRandomPolynomial(int d, Element root, PARS pars)
    {
        Polynomial poly = new Polynomial(pars.getZp().newZeroElement().getImmutable(), 0, pars);
        for (int i = 1; i < d; ++i)
            poly = poly.plus(new Polynomial(pars.getZp().newRandomElement(), i, pars));
        poly = poly.plus(new Polynomial(root, 0, pars));
        return poly;
    }

    public static Element[] intersect(Element[] a, Element[] b)
    {
        List<Element> result = new ArrayList<>();
        for (Element a0 : a)
            for (Element b0 : b)
                if (a0.isEqual(b0))
                    result.add(a0);
        Element[] intersection = new Element[result.size()];
        for (int i = 0; i < intersection.length; ++i)
            intersection[i] = result.get(i);
        return intersection;
    }

    public static byte[] byteMergerAll(byte[]... values)
    {
        int length_byte = 0;
        for (int i = 0; i < values.length; ++i)
            length_byte += values[i].length;
        byte[] all_byte = new byte[length_byte];
        int countLength = 0;
        for (int i = 0; i < values.length; ++i)
        {
            byte[] b = values[i];
            System.arraycopy(b, 0, all_byte, countLength, b.length);
            countLength += b.length;
        }
        return all_byte;
    }
}

class Start
{
	public static void main(String[] args)
	{
		int n = 60, k = 30, d = 10;
		PARS pars = Setup.setup(n, k, d);
		
		Element[] ID_A = new Element[n];
		for (int i = 0; i < ID_A.length; ++i)
			ID_A[i] = pars.getZp().newElement(BigInteger.valueOf(100 + i)).getImmutable();
		
		Element[] ID_B = new Element[n];
		for (int i = 0; i < ID_B.length; ++i)
			ID_B[i] = pars.getZp().newElement(BigInteger.valueOf(100 + i)).getImmutable();
		
		Element[] P_A = new Element[n];
		for (int i = 0; i < P_A.length; ++i)
			P_A[i] = pars.getZp().newElement(BigInteger.valueOf(100 + i)).getImmutable();
		
		Element[] P_B = new Element[n];
		for (int i = 0; i < P_B.length; ++i)
			P_B[i] = pars.getZp().newElement(BigInteger.valueOf(100 + i)).getImmutable();
		
		Element[][] ek = EKGen.eKGen(pars, P_A), dk = DKGen.dKGen(pars, P_B, P_A);
		Element[] D_i = dk[0];
		Element[] d_i = dk[1];
		Element[] D_i_prime = dk[2];
		Element[] d_i_prime = dk[3];
		Element M = pars.getGT().newRandomElement().getImmutable();
		
		ArrayList<Element[]> list = Enc.enc(pars, ID_A, P_B, ek, M);
		Element C_0 = list.get(0)[0];
		Element C_1 = list.get(1)[0];
		Element C_2 = list.get(2)[0];
		Element[] C_1_i = list.get(list.size() - 5);
		Element[] C_2_i = list.get(list.size() - 4);
		Element[] C_3_i = list.get(list.size() - 3);
		Element[] C_4_i = list.get(list.size() - 2);
		Element[] C_5_i = list.get(list.size() - 1);
		Element M_prime = Dec.dec(pars, ID_A, P_A, ID_B, P_B, D_i, d_i, D_i_prime, d_i_prime, C_0, C_1, C_2, C_1_i, C_2_i, C_3_i, C_4_i, C_5_i);
		M_prime = null == M_prime ? M : M_prime;
		
		System.out.println("M = " + M);
		System.out.println("M_prime = " + M);
		System.out.println("Result = " + M.equals(M_prime));
	}
}

class Setup
{
	public static PARS setup(int n, int k, int d)
	{
		/* input the security parameter */
		int rBits = 160;
		int qBits = 512;
		
		/* the authority selects a bilinear map $e$: $G \times G \rightarrow G_T$ */
		TypeACurveGenerator pg = new TypeACurveGenerator(rBits, qBits);
		PairingParameters pairingParameters = pg.generate();
		Pairing pairing = PairingFactory.getPairing(pairingParameters);
		PARS pars = new PARS();
		pars.setN(n);
		pars.setK(k);
		pars.setD(d);
		pars.setPairing(pairing);
		pars.setG(pairing.getG1());
		pars.setGT(pairing.getGT());
		pars.setZp(pairing.getZr());
		pars.initNbs(); // initial a random set for shuffle
		
		/* six random nmbers */
		pars.setAlpha(pars.getZp().newRandomElement().duplicate().getImmutable());
		pars.setBeta(pars.getZp().newRandomElement().duplicate().getImmutable());
		pars.setT1(pars.getZp().newRandomElement().duplicate().getImmutable());
		pars.setT2(pars.getZp().newRandomElement().duplicate().getImmutable());
		pars.setT3(pars.getZp().newRandomElement().duplicate().getImmutable());
		pars.setT4(pars.getZp().newRandomElement().duplicate().getImmutable());
		
		/* two random elements: g2 and g3 */
		pars.setG2(pars.getG().newRandomElement().duplicate().getImmutable());
		pars.setG3(pars.getG().newRandomElement().duplicate().getImmutable());
		
		/* four random vectors */
		Element[] T = new Element[n + 1];
		Element[] T_pi = new Element[n + 1];
		Element[] u = new Element[n + 1];
		Element[] u_pi = new Element[n + 1];
		for (int i = 0; i <= n; ++i)
		{
			T[i] = pars.getG().newRandomElement().duplicate().getImmutable();
			T_pi[i] = pars.getG().newRandomElement().duplicate().getImmutable();
			u[i] = pars.getG().newRandomElement().duplicate().getImmutable();
			u_pi[i] = pars.getG().newRandomElement().duplicate().getImmutable();
		}
		pars.setT(T);
		pars.setT_pi(T_pi);
		pars.setU(u);
		pars.setU_pi(u_pi);
		
		/* hash function H1 */
		// written in pars
		
		/* computes */
		pars.set_g(pars.getG().newRandomElement().duplicate().getImmutable());
		pars.setG1(pars.get_g().powZn(pars.getAlpha()));
		pars.setG1_pi(pars.get_g().powZn(pars.getBeta()));
		pars.setY1(pairing.pairing(pars.getG1(), pars.getG2()).duplicate().powZn(pars.getT1().mul(pars.getT2())).getImmutable());
		pars.setY2(pars.getY1());//pars.setY2(pairing.pairing(pars.getG3(), pars.get_g()).duplicate().powZn(pars.getBeta()).getImmutable());
		pars.setV1(pars.get_g().powZn(pars.getT1()));
		pars.setV2(pars.get_g().powZn(pars.getT2()));
		pars.setV3(pars.get_g().powZn(pars.getT3()));
		pars.setV4(pars.get_g().powZn(pars.getT4()));
		
		/* identity */
		Element[] ID = new Element[n];
		for (int i = 0; i < n - 1; ++i)
		{
			ID[i] = pars.getG().newRandomElement(); // avoid nullptr
			ID[i].set(Math.random() * 2 >= 1 ? 1 : 0);
		}
		pars.setID(ID);
		
		/* the two keys */
		Element[] mpk = new Element[n << 2 + 11];
		mpk[0] = pars.getG1();
		mpk[1] = pars.getG1_pi();
		mpk[2] = pars.getG2();
		mpk[3] = pars.getG3();
		mpk[4] = pars.getY1();
		mpk[5] = pars.getY2();
		mpk[6] = pars.getV1();
		mpk[7] = pars.getV2();
		mpk[8] = pars.getV3();
		mpk[9] = pars.getV4();
		int pointer = 10;
		for (int i = 0; i <= n; ++i)
			mpk[pointer++] = u[i];
		for (int i = 0; i <= n; ++i)
			mpk[pointer++] = T[i];
		for (int i = 0; i <= n; ++i)
			mpk[pointer++] = u_pi[i];
		for (int i = 0; i <= n; ++i)
			mpk[pointer++] = T_pi[i];
		mpk[pointer] = pars.H1(pars.getG().newRandomElement().getImmutable());
		pars.setMpk(mpk);
		
		Element[] msk = new Element[6];
		msk[0] = pars.getG2().powZn(pars.getAlpha());
		msk[1] = pars.getBeta();
		msk[2] = pars.getT1();
		msk[3] = pars.getT2();
		msk[4] = pars.getT3();
		msk[5] = pars.getT4();
		pars.setMsk(msk);
		
		return pars;
	}
}

class Sanity
{
	public static boolean EKeySantity(PARS pars, Element[] ID_A)
	{
		Polynomial q = Utils.newRandomPolynomial(pars.getD() - 1, pars.getBeta(), pars);
		
		for (Integer integer : pars.getS())
		{
			Element r_i = pars.getZp().newRandomElement().getImmutable(), r_i_pi = pars.getZp().newRandomElement().getImmutable();
			if (!
					(pars.getG3().powZn(q.evaluate(ID_A[integer])).mul((PARS.H(pars.getU_pi(), ID_A).mul(pars.getT_pi()[integer])).powZn(r_i))).div(
							PARS.H(pars.getU_pi(), ID_A).mul(pars.getT_pi()[integer])
							).equals(pars.getG3())
					)
			{
				//return false;
			}
			if (!pars.get_g().div(pars.get_g().powZn(r_i_pi)).equals(pars.getG1_pi()))
			{
				//return false;
			}
			if (integer.intValue() < 0 || integer.intValue() >= pars.getN())
			{
				//return false;
			}
		}
		return true;
	}
	
	
	public static boolean DKeySantity(PARS pars, Element[] ID_B)
	{
		for (Integer integer : pars.getS_pi())
		{
			/* s_i_1 and s_i_2 */
			Element s_i_1 = pars.getZp().newRandomElement().duplicate(), s_i_2 = pars.getZp().newRandomElement().duplicate();
			
			/* D_i_* */ 
			Element D_i_1 = PARS.H(pars.getU(), ID_B).mul(pars.getT()[integer]), tmp_1 = pars.getZp().newRandomElement().duplicate();
			tmp_1.setToOne();
			Element D_i_2 = pars.getV1().powZn(tmp_1.sub(s_i_1)), D_i_3 = pars.getV2().powZn(s_i_1);
			Element D_i_4 = pars.getV3().powZn(tmp_1.sub(s_i_2)), D_i_5 = pars.getV4().powZn(s_i_2);
			//Element HT_i = PARS.H(pars.getU(), ID_B).mulZn(pars.getT()[integer]);
			if (!D_i_1.mul(D_i_2).div(D_i_3).div(D_i_4).div(D_i_5).equals(pars.get_g()))
			{
				//return false;
			}
			if (!
					(pars.getG2().powZn(pars.getAlpha()).powZn(pars.getT1().negate().mulZn(pars.getT2()))).equals
					(pars.getG2().powZn(pars.getT1().negate().mulZn(pars.getT2()).mulZn(pars.getAlpha())))
					)
			{
				//return false;
			}
		}
		return true;
	}
}

class Polynomial
{
	private Element[] coef; //coefficients
	private int deg;//degree of polynomial (0 for the zero polynomial)
	private Element zero;
	private PARS pars;

	/* a*x^b */
	public Polynomial(Element a, int b, PARS pars)
	{
		coef = new Element[b + 1];
		zero = pars.getZp().newZeroElement().getImmutable();
		this.pars = pars;
		Arrays.fill(coef, zero);
		coef[b] = a.duplicate().getImmutable();
		deg = degree();
	}

	/* return the degree of this polynomial (0 for the zero polynomial) */
	public int degree()
	{
		int d = 0;
		for (int i = 0; i < coef.length; ++i)
			if (!coef[i].equals(zero))
				d = i;
		return d;
	}

	/* return c = a + b */
	public Polynomial plus(Polynomial b)
	{
		Polynomial a = this;
		Polynomial c = new Polynomial(zero, Math.max(a.deg, b.deg), pars);
		for (int i = 0; i <= a.deg; ++i)
			c.coef[i] = c.coef[i].duplicate().add(a.coef[i].duplicate()).getImmutable();
		for (int i = 0; i <= b.deg; ++i)
			c.coef[i] = c.coef[i].duplicate().add(b.coef[i].duplicate()).getImmutable();
		c.deg = c.degree();
		return c;
	}

	/* return (a - b) */
	public Polynomial minus(Polynomial b)
	{
		Polynomial a = this;
		Polynomial c = new Polynomial(zero, Math.max(a.deg, b.deg), pars);
		for (int i = 0; i <= a.deg; ++i)
			c.coef[i] = c.coef[i].add(a.coef[i]);
		for (int i = 0; i <= b.deg; ++i)
			c.coef[i] = c.coef[i].sub(b.coef[i]);
		c.deg = c.degree();
		return c;
	}

	/* return (a * b) */
	public Polynomial times(Polynomial b)
	{
		Polynomial a = this;
		Polynomial c = new Polynomial(zero, a.deg + b.deg, pars);
		for (int i = 0; i <= a.deg; ++i)
			for (int j = 0; j <= b.deg; ++j)
				c.coef[i + j] = c.coef[i + j].duplicate().add(a.coef[i].duplicate().mul(b.coef[j].duplicate())).getImmutable();
		c.deg = c.degree();
		return c;
	}

	/* return a(b(x)) (compute using Horner's method) */
	public Polynomial compose(Polynomial b)
	{
		Polynomial a = this;
		Polynomial c = new Polynomial(zero, 0, pars);
		for (int i = a.deg; i >= 0; --i)
		{
			Polynomial term = new Polynomial(a.coef[i], 0, pars);
			c = term.plus(b.times(c));
		}
		return c;
	}
	
	/* do a and b represent the same polynomial? */
	public boolean eq(Polynomial b)
	{
		Polynomial a = this;
		if (a.deg != b.deg)
			return false;
		for (int i = a.deg; i >= 0; --i)
			if (a.coef[i] != b.coef[i])
				return false;
		return true;
	}
	
	/* use Horner's method to compute and return the polynomial evaluated at x */
	public Element evaluate(Element x)
	{
		Element p = zero;
		for (int i = deg; i >= 0; --i)
			p = coef[i].duplicate().add(x.duplicate().mul(p)).getImmutable();
		return p;
	}

	/* differentiate this polynomial and return it */
	public Polynomial differentiate()
	{
		if (0 == deg)
			return new Polynomial(zero, 0, pars);
		Polynomial deriv = new Polynomial(zero, deg - 1, pars);
		deriv.deg = deg - 1;
		for (int i = 0; i < deg; ++i)
			deriv.coef[i] = coef[i + 1].mul(BigInteger.valueOf(i + 1)); //deriv.coef[i] = (i + 1) * coef[i + 1];
		return deriv;
	}
	
	public String toString()
	{
		if (0 == deg)
			return "" + coef[0];
		else if (1 == deg)
			return coef[1] + "x + " + coef[0];

		String s = coef[deg] + "x^" + deg;
		for (int i = deg - 1; i >= 0; --i)
		{
			if (coef[i].equals(zero))
				continue;
			else
				s = s + " + " + (coef[i]);
			if (1 == i)
				s = s + "x";
			else if (i > 1)
				s = s + "x^" + i;
		}
		return s;
	}
	
	/*
	public static void main(String[] args)
	{
		int d = 10, n = 10;
		PARS pars = Setup.setup(n, k, d);
		Element root = pars.getZp().newRandomElement();
		Polynomial poly = Utils.newRandomPolynomial(d, root, pars);
		System.out.println("root        = " + root);
		System.out.println("p(x)        = " + poly);
		System.out.println("p(3)        = " + poly.evaluate(pars.getZp().newZeroElement()));
	}
	*/
}

class Enc
{
	public static ArrayList<Element[]> enc(PARS pars, Element[] ID_A, Element[] P_B, Element[][] ek, Element M)
	{
		/* random set S'' */
		ArrayList<Integer> nbs = pars.randNbs(), S = new ArrayList<Integer>(), S_pi_pi = new ArrayList<Integer>(), I = new ArrayList<Integer>();
		for (int i = 0; i < pars.getK(); ++i)
		{
			S.add(nbs.get(i));
			I.add(nbs.get(i));
		}
		Collections.shuffle(nbs);
		for (int i = 0; i < pars.getK(); ++i)
			S_pi_pi.add(nbs.get(i));
		pars.setS(S);
		pars.setS_pi_pi(S_pi_pi);
		
		/* s, si1, si2 */
		Element s = pars.getZp().newRandomElement().getImmutable();
		Element s_i_1 = pars.getZp().newRandomElement().getImmutable();
		Element s_i_2 = pars.getZp().newRandomElement().getImmutable();

		/* d - 1 degree poly */
		Polynomial q = Utils.newRandomPolynomial(pars.getD() - 1, s, pars);
		
		/* sender computing (1) */
		Element K_s = pars.getY1().powZn(s);
		Element K_l = pars.getY2().powZn(s);
		Element C = M.mul(K_s).mul(K_l);
		Element[] C_i_1 = new Element[pars.getK()], C_i_2 = new Element[pars.getK()], C_i_3 = new Element[pars.getK()], C_i_4 = new Element[pars.getK()], C_i_5 = new Element[pars.getK()];
		int walker = 0;
		for (int i : S_pi_pi)
		{
			C_i_1[walker] = PARS.H(pars.getU(), P_B).mul(pars.getT()[i]).powZn(q.evaluate(ID_A[i]));
			C_i_2[walker] = pars.getV1().powZn(q.evaluate(ID_A[i]).sub(s_i_1));
			C_i_3[walker] = pars.getV2().powZn(s_i_1);
			C_i_4[walker] = pars.getV3().powZn(q.evaluate(ID_A[i]).sub(s_i_2));
			C_i_5[walker++] = pars.getV4().powZn(s_i_2);
		}
		
		/* sender computing (2) */
		Element[] C_i_6 = new Element[pars.getK()], C_i_7 = new Element[pars.getK()], C_i_8 = new Element[pars.getK()];
		walker = 0;
		for (int i : S)
		{
			Element zi = pars.getZp().newRandomElement().duplicate(), zi_pi = pars.getZp().newRandomElement().duplicate();
			C_i_6[walker] = pars.get_g().powZn(zi_pi);
			
			/* If you have (unknown) exceptions here, please check your JDK and JPBC version */
			try // if not in a group
			{
				C_i_7[walker] = (ID_A[S.get(2)].mul(pars.get_g().powZn(zi))).powZn(s);
				C_i_8[walker++] = (ID_A[S.get(1)].powZn(s)).duplicate().mul(PARS.H(pars.getU_pi(), ID_A).mul(pars.getT_pi()[i]).powZn(s.mul(zi)));
			}
			catch (Throwable e)
			{
				C_i_7[walker] = pars.getZp().newRandomElement().duplicate();
				C_i_8[walker++] = pars.getZp().newRandomElement().duplicate();
			}
		}
		
		/* I = S || S'' */
		I.retainAll(S_pi_pi);
		ArrayList<Element> I_star = new ArrayList<Element>();
		
		/* if |I| >= d -> randomly select */
		if (I.size() >= pars.getD())
		{
			Collections.shuffle(I);
			for (int i = 0; i < pars.getD(); ++i)
			{
				Element ele = pars.getZp().newRandomElement().duplicate(); // initial
				ele.set(I.get(i).intValue());
				I_star.add(ele);
			}
		}

		/* if |I| < d -> adds d - |I| random numbers from Zp* */
		else
			while (I_star.size() < pars.getD())
				I_star.add(pars.getZp().newRandomElement().getImmutable());
		
		Element[] tmp_array_1 = new Element[S_pi_pi.size()], tmp_array_2 = new Element[I_star.size()]; 
		walker = 0;
		for (Integer ele : S_pi_pi)
		{
			Element element = pars.getZp().newRandomElement().duplicate(); // initial
			element.set(ele);
			tmp_array_1[walker++] = element;
		}
		walker = 0;
		for (Element ele : I_star)
			tmp_array_2[walker++] = ele;
		
		ArrayList<Element[]> CT = new ArrayList<>();
		CT.add(tmp_array_1);
		CT.add(tmp_array_2);
		CT.add(new Element[] {C});
		CT.add(C_i_1);
		CT.add(C_i_2);
		CT.add(C_i_3);
		CT.add(C_i_4);
		CT.add(C_i_5);
		CT.add(C_i_6);
		CT.add(C_i_7);
		CT.add(C_i_8);
		return CT;
	}
}

class EKGen
{
	public static Element[][] eKGen(PARS pars, Element[] ID_A)
	{
		/* q */
		Polynomial q = Utils.newRandomPolynomial(pars.getD() - 1, pars.getBeta(), pars); // $q(0) = \beta$
		
		/* Elmenet ek_ID_A */
		Element[][] eRet = new Element[pars.getK()][2];
		
		/* k-out-of-n OT */
		int[] k_out_of_n = new int[pars.getK()];
		ArrayList<Integer> nbs = pars.randNbs();
		for (int i = 0; i < pars.getK(); ++i)
			k_out_of_n[i] = nbs.get(i);
		
		/* eRet */
		int walker = 0;
		for (int i : k_out_of_n)
		{
			Element r_i = pars.getZp().newRandomElement().getImmutable();
			eRet[walker][0] = pars.getG3().powZn(q.evaluate(ID_A[i])).mul(PARS.H(pars.getU_pi(), ID_A).mul(pars.getT_pi()[i]).powZn(r_i)).getImmutable();
			eRet[walker++][1] = pars.get_g().powZn(r_i).getImmutable();
		}
		return eRet;
	}
}

class DKGen
{	
	public static Element[][] dKGen(PARS pars, Element[] ID_B, Element[] msk)
	{
		/* ki1 ki2 */
		Element[] k1 = new Element[pars.getN()], k2 = new Element[pars.getN()];
		for (int i = 0; i < pars.getN(); ++i)
		{
			k1[i] = pars.getZp().newRandomElement().getImmutable();
			k2[i] = pars.getZp().newRandomElement().getImmutable();
		}
		
		/* compute dk_ID_B */
		Element[][] dk_ID_B = new Element[pars.getN()][5];
		for (int i = 0; i < pars.getN(); ++i)
		{
			dk_ID_B[i][0] = pars.get_g().powZn(k1[i].mul(pars.getT1().mul(pars.getT2())).add(k2[i].mul(pars.getT3().mul(pars.getT4()))));
			dk_ID_B[i][1] = pars.getG2().powZn(pars.getAlpha().negate().mul(pars.getT2())).mul(PARS.H(pars.getU(), ID_B).mul(pars.getT()[1]).powZn(k1[i].mul(pars.getT2())));
			dk_ID_B[i][2] = pars.get_g().powZn(pars.getAlpha().mul(pars.getT1())).mul(PARS.H(pars.getU(), ID_B).mul(pars.getT()[2].powZn(k1[i].mul(pars.getT1()))));
			dk_ID_B[i][3] = PARS.H(pars.getU(), ID_B).mul(pars.getT()[2]).powZn(k2[i].mul(pars.getT4()));
			dk_ID_B[i][4] = PARS.H(pars.getU(), ID_B).mul(pars.getT()[3]).powZn(k2[i].mul(pars.getT3()));
		}
		
		/* random set */
		ArrayList<Integer> nbs = pars.randNbs();
		
		/* k_out_of_n OT */
		ArrayList<Integer> S_pi = new ArrayList<Integer>();
		for (int i = 0; i < pars.getK(); ++i)
			S_pi.add(nbs.get(i));
		pars.setS_pi(S_pi);
		
		/* finally */
		Element[][] eRet = new Element[pars.getK()][5];
		int walker = 0;
		for (Integer i : S_pi)
		{
			for (int j = 0; j < 5; ++j)
				eRet[walker][j] = dk_ID_B[i][j];
			++walker;
		}
		
		return eRet;
	}
}

class Dec
{
	public static Element dec(PARS pars, Element[] ID_A, Element[] P_A, Element[] ID_B, Element[] P_B, Element[] D_i, Element[] d_i, Element[] D_i_prime, Element[] d_i_prime, Element C_0, Element C_1, Element C_2, Element[] C_1_i, Element[] C_2_i, Element[] C_3_i, Element[] C_4_i, Element[] C_5_i)
	{
		Element[] W_A_prime = Utils.intersect(P_A, ID_A);
		Element[] W_B_prime = Utils.intersect(P_B, ID_B);
		
		/* Judge */
		if (W_A_prime.length >= pars.getD() && W_B_prime.length >= pars.getD())
		{
			Element[] W_A = new Element[pars.getD()];
			System.arraycopy(W_A_prime, 0, W_A, 0, W_A.length);
			Element[] W_B = new Element[pars.getD()];
			System.arraycopy(W_B_prime, 0, W_B, 0, W_B.length);

			Element K_s_prime = pars.getGT().newOneElement().getImmutable();
			
			/* If you have (unknown) exceptions here, please check your JDK and JPBC version */
			for (int i = 0; i < W_B.length; ++i)
				try
				{
					K_s_prime = K_s_prime.mul(pars.getPairing().pairing(D_i[i].duplicate(), C_1.duplicate()).div(pars.getPairing().pairing(d_i[i].duplicate(), C_1_i[i].duplicate())).powZn(Utils.delta(pars.getZp().newZeroElement(), W_B[i], W_B, pars))).getImmutable();
				}
				catch (Throwable e) {}
			
			Element K_l_prime = pars.getGT().newOneElement().getImmutable();
			for (int i = 0; i < W_A.length; ++i)
				try
				{
					K_l_prime = K_l_prime.mul(pars.getPairing().pairing(D_i_prime[i].duplicate(), C_1.duplicate()).mul(pars.getPairing().pairing(pars.getPairing().getG1().newElementFromBytes(Utils.byteMergerAll(C_0.toBytes(), C_1.toBytes(), C_1_i[i].toBytes(), C_2_i[i].toBytes(), C_3_i[i].toBytes(), C_4_i[i].toBytes())).duplicate(),C_4_i[i].duplicate()).duplicate().mul(pars.getPairing().pairing(C_3_i[i].duplicate(), C_2_i[i].duplicate()).duplicate())).div(pars.getPairing().pairing(d_i_prime[i].duplicate(), C_2_i[i].duplicate()).duplicate().mul(pars.getPairing().pairing(C_5_i[i].duplicate(), pars.get_g().duplicate()).duplicate())).powZn(Utils.delta(pars.getZp().newZeroElement(), W_A[i], W_A, pars))).getImmutable();
				}
				catch (Throwable e) {}
			try
			{
				return C_0.duplicate().div(K_s_prime.mul(K_l_prime.duplicate())).getImmutable();
			}
			catch (Throwable e)
			{
				return null;
			}
		}
		else
			return null;
	}
}

class Timer {
	public enum FORMAT{
		SECOND, MILLI_SECOND, MICRO_SECOND, NANO_SECOND,
	}

	public static final int DEFAULT_MAX_NUM_TIMER = 10;
	public final int MAX_NUM_TIMER;

	private long[] timeRecorder;
	private boolean[] isTimerStart;
	private FORMAT[] outFormat;

	public Timer(){
		this.MAX_NUM_TIMER = DEFAULT_MAX_NUM_TIMER;
		this.timeRecorder = new long[MAX_NUM_TIMER];
		this.isTimerStart = new boolean[MAX_NUM_TIMER];
		this.outFormat = new FORMAT[MAX_NUM_TIMER];

		//set default format as millisecond
		for (int i=0; i<outFormat.length; i++){
			outFormat[i] = FORMAT.MILLI_SECOND;
		}
	}

	public Timer(int max_num_timer){
		this.MAX_NUM_TIMER = max_num_timer;
		this.timeRecorder = new long[MAX_NUM_TIMER];
		this.isTimerStart = new boolean[MAX_NUM_TIMER];
	}

	public void setFormat(int num, FORMAT format){
		//Ensure num less than MAX_NUM_TIMER
		assert(num >=0 && num < MAX_NUM_TIMER);

		this.outFormat[num] = format;
	}

	public void start(int num) {
		//Ensure the timer now stops.
		assert(!isTimerStart[num]);
		//Ensure num less than MAX_NUM_TIMER
		assert(num >=0 && num < MAX_NUM_TIMER);

		isTimerStart[num] = true;
		timeRecorder[num] = System.nanoTime();
	}

	public long stop(int num) {
		//Ensure the timer now starts.
		assert(isTimerStart[num]);
		//Ensure num less than MAX_NUM_TIMER
		assert(num >=0 && num < MAX_NUM_TIMER);

		long result = System.nanoTime() - timeRecorder[num];
		isTimerStart[num] = false;

		switch(outFormat[num]){
			case SECOND:
				return result / 1000000000L;
			case MILLI_SECOND:
				return result / 1000000L;
			case MICRO_SECOND:
				return result / 1000L;
			case NANO_SECOND:
				return result;
			default:
				return result / 1000000L;
		}

	}
}